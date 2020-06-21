"""
This file contains the code running in the back end of GesturePad.
"""

import os
import imageio
import math

from utils.config_helper import read_config
from backend.recording.audio import Audio
from backend.recording.video import Video
from backend.mediapipe.mediapipe_helper import MediaPipeHelper
from backend.mediapipe.gesture_identifier import GestureIdentifier
from backend.clients.speech import SpeechClient
from backend.clients.gestures import Gesture, GESTURE_PAIR, GestureClient
from backend.fusion.multimodal_types import ModalityOutput, AudioInput, WordOutput, VideoInput, GestureOutput
from backend.fusion.multimodal_fuser import GesturePadFuser
from backend.export.formats import HTMLFormat

from typing import Tuple, List, Any, Optional


class Backend:

    def __init__(self,
                 mediapipe_dir: str,
                 audio_path: str,
                 video_path: str,
                 mp_video_path: str,
                 gestures_dir: str,
                 gesture_prefix: str,
                 root_window: Optional[Any] = None,
                 debug: bool = False):
        """
        Implements the back end of GesturePad, linking all modules together in the intended flow.
        :param mediapipe_dir: Path to the Google MediaPipe installation directory
        :param audio_path: Path to the audio file to write after recording
        :param video_path: Path to the video file to write after recording
        :param mp_video_path: Path to the video file to write after Google MediaPipe processing
        :param gestures_dir: Path to the directory wherein to store detected gestures
        :param gesture_prefix: Prefix in naming gesture files
        :param root_window: Tkinter root window (if any)
        :param debug: Whether to print debug information and keep intermediate files for inspection (default: False)
        """

        if not os.path.exists(gestures_dir):
            raise FileNotFoundError("Invalid gesture directory.")
        elif not os.path.isdir(gestures_dir):
            raise NotADirectoryError("The path provided as gestures directory is not a directory.")

        self.__debug = debug
        self.__root_window = root_window

        self.__mediapipe_dir = mediapipe_dir
        self.__audio_path = audio_path
        self.__video_path = video_path
        self.__mp_video_path = mp_video_path
        self.__gestures_dir = gestures_dir
        self.__gesture_prefix = gesture_prefix

        self.__mediapipe = MediaPipeHelper(mediapipe_dir=self.__mediapipe_dir)
        self.__gesture_client = GestureClient()
        self.__speech_client = SpeechClient()
        self.__fuser = GesturePadFuser(sync_tolerance=0.15)
        self.__format = HTMLFormat()

        # Internal state
        self.__recording = False
        self.__waiting_audio = False

    # --- Recording ---
    def start_recording(self,
                        video_fps: float = 6,
                        video_resolution: Tuple[int, int] = (640, 480),
                        max_audio_length: int = 5*60
                        ) -> (Video, Audio):
        """
        Starts recording audio and video in an asynchronous fashion.
        :param video_fps: FPS to use when recording videos
        :param video_resolution: Resolution to use when recording videos (format: width x height)
        :param max_audio_length: Maximum length when recording audio files
        :return: Tuple containing at positions:
                - 0: Video object representing the video recording helper
                - 1: Audio object representing the audio recording helper
        """

        try:
            os.remove(self.__video_path)
            os.remove(self.__audio_path)
        except FileNotFoundError:
            pass

        audio_rec = Audio(path=self.__audio_path)
        audio_rec.rec(max_audio_length)

        video_rec = Video(path=self.__video_path,
                          fps=video_fps,
                          resolution=video_resolution,
                          root_window=self.__root_window)
        video_rec.start()

        self.__recording = True

        return video_rec, audio_rec

    def stop_recording(self, video_recorder: Video, audio_recorder: Audio) -> (VideoInput, AudioInput):
        """
        Stops the previously started recordings, returning the recorded files.
        :param video_recorder: Video object representing the video recording helper
        :param audio_recorder: Audio object representing the audio recording helper
        :return: Tuple containing at positions:
                - 0: VideoInput object representing the recorded video
                - 1: AudioInput object representing the recorded audio
        :raises RuntimeError if no recording has been started
        """

        if not self.__recording:
            raise RuntimeError("There is no ongoing recording.")

        video_recorder.stop()
        audio_recorder.stop()
        self.__recording = False

        # Read stats from video file
        video_reader = imageio.get_reader(self.__video_path)
        video_metadata = video_reader.get_meta_data()
        v_input = VideoInput(path=self.__video_path,
                             length=video_metadata["duration"],
                             fps=video_metadata["fps"],
                             resolution=video_metadata["size"])

        # Read stats from audio file
        a_input = AudioInput(path=self.__audio_path,
                             length=audio_recorder.get_real_duration(),
                             bit_rate=16_000)

        # Align audio and video files
        delay = math.floor(a_input.length - v_input.length)
        audio_recorder.trim(int(delay * 1000))

        return v_input, a_input
    # --- --- ---

    # --- Audio/video processing ---
    def preprocess_video(self, video_input: VideoInput) -> Tuple[List[str], List[float]]:
        """
        Preprocess the video by running Google MediaPipe on it, then extracting stable frames.
        :param video_input: VideoInput object representing the recorded video
        :return: Tuple containing at positions:
                - 0: List of paths to stable frames stored on disk
                - 1: List of timings associated with stable frames
        """

        # Google MediaPipe preprocessing
        self.__mediapipe.run(input_dir=os.path.abspath(video_input.path),
                             output_dir=os.path.abspath(self.__mp_video_path))

        if not self.__debug:
            os.remove(self.__video_path)

        # Run GestureIdentifier
        gesture_identifier = GestureIdentifier(video_path=self.__mp_video_path,
                                               stable_frames=5,
                                               instability_threshold=2.5,
                                               gesture_frames_interval=3,
                                               gesture_time_interval=2,
                                               black_threshold=0.995,
                                               ln_norm=3,
                                               prev_gesture_threshold=0.01,
                                               debug=self.__debug)

        stable_frames = gesture_identifier.process()
        if not self.__debug:
            os.remove(self.__mp_video_path)

        frame_paths = []
        frame_timings = []
        for i, (frame, timing) in enumerate(stable_frames):
            path = os.path.join(self.__gestures_dir,
                                "{pref}{i}.jpeg".format(pref=self.__gesture_prefix, i=i))
            imageio.imwrite(path, frame)
            frame_paths.append(path)
            frame_timings.append(timing)

        return frame_paths, frame_timings

    def process_video(self, frame_paths: List[str], gesture_timings: List[float]) -> List[GestureOutput]:
        """
        Classifies the given images in a synchronous fashion.
        :param frame_paths: List of paths to stable frame files to classify
        :param gesture_timings: List of timings associated with each Gesture (obtained from preprocess_video)
        :return: List of GestureOutput objects (Gesture, timing pairs)
        """

        recognized_gestures = self.__gesture_client.process_images(image_paths=frame_paths)

        if not self.__debug:
            for path in frame_paths:
                try:
                    os.remove(path)
                except RuntimeError:
                    pass

        processed_gestures = []
        for gesture, timing in zip(recognized_gestures, gesture_timings):
            processed_gestures.append(GestureOutput(gesture=gesture, timing=timing))

        return processed_gestures

    def send_audio(self, audio_input: AudioInput) -> Any:
        """
        Sends a file for word recognition in an asynchronous fashion.
        :param audio_input: AudioInput object representing the recorded audio
        :return: google.longrunning.Operation object to later poll for response
        """

        operation = self.__speech_client.process_audio(audio_path=audio_input.path)
        self.__waiting_audio = True

        if not self.__debug:
            try:
                os.remove(audio_input.path)
            except RuntimeError:
                pass

        return operation

    def process_audio_response(self, operation: Any) -> List[WordOutput]:
        """
        Waits for the recognized words from a previous send_audio request.
        :param operation: google.longrunning.Operation object to wait completion for (obtained from send_audio)
        :return: List of WordOutput objects (string, start_time, end_time associations)
        """

        if not self.__waiting_audio:
            raise RuntimeError("There is no ongoing cloud audio processing.")

        recognized_words = self.__speech_client.get_words(operation)
        self.__waiting_audio = False

        return [*map(lambda x: WordOutput(word=x[0], timing=x[1], end_timing=x[2]), recognized_words)]
    # --- --- ---

    # --- Multimodal fusion, formatting ---
    def fuse(self, gestures: List[GestureOutput], words: List[WordOutput]) -> List[ModalityOutput]:
        """
        Fuses audio and video modalities tokens, providing a single ordering among words and gestures.
        :param gestures: Recognized gestures (from process_video_response)
        :param words: Recognized words (from process_audio_response)
        :return: List containing ordered words and gestures
        """

        return self.__fuser.fuse(words, gestures)

    def apply_format(self, multimodal_stream: List[ModalityOutput]) -> List[str]:
        """
        Uses formatting rules for a textual format (i.e. HTML) to produce the output as a string.
        :param multimodal_stream: List containing ordered words and gestures
        :return: List of strings representing the formatted vocal input
        """

        processed_stream = []
        gesture_queue = []
        caps_lock = False
        for token in multimodal_stream:
            utterance = token.utterance

            # Gestures
            if type(token) == GestureOutput:
                # Handle gestures that work in pairs in a queue
                if utterance in GESTURE_PAIR:
                    if len(gesture_queue) > 0 and gesture_queue[-1].utterance == utterance:
                        gesture_queue = gesture_queue[:-1]

                        if utterance != Gesture.CAPS_LOCK:
                            processed_stream.append(self.__format(utterance, close=True))
                        else:
                            caps_lock = False
                    else:
                        gesture_queue.append(token)
                        if utterance != Gesture.CAPS_LOCK:
                            processed_stream.append(self.__format(utterance, close=False))
                        else:
                            caps_lock = True

            # Words
            else:
                processed_stream.append(str.upper(utterance) if caps_lock else utterance)

        return processed_stream
    # --- --- ---


if __name__ == '__main__':
    c, _ = read_config()

    b = Backend(mediapipe_dir=c["mediapipe_dir"],
                audio_path="../tmp/integration_audio.wav",
                video_path="../tmp/integration_video.mp4",
                mp_video_path="../tmp/integration_video_mp.mp4",
                gestures_dir="../tmp/integration_frames",
                gesture_prefix="image",
                debug=False)

    # Recording tests
    v, a = b.start_recording()
    v, a = b.stop_recording(v, a)
    # OK

    # Preprocessing tests
    frames, timings = b.preprocess_video(v)
    # OK

    # Cloud requests tests
    words_op = b.send_audio(audio_input=a)
    g_list = b.process_video(frame_paths=frames, gesture_timings=timings)
    print([(x.utterance, x.timing) for x in g_list])
    # OK

    # Cloud response tests
    w_list = b.process_audio_response(operation=words_op)
    print([(x.utterance, x.timing, x.params["end_time"]) for x in w_list])
    # OK

    # Multimodal fusion tests
    fused = b.fuse(gestures=g_list, words=w_list)
    formatted = b.apply_format(multimodal_stream=fused)
    print(formatted)
    # OK
