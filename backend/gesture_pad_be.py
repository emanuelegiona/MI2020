"""
This file contains the code running in the back end of GesturePad.
"""

import os
import imageio
import math

from utils.config_helper import read_config
from recording import Audio, Video
from mediapipe import MediaPipeHelper, GestureIdentifier
from clients import SpeechClient, GestureClient
from fusion import AudioInput, WordOutput, VideoInput, GestureOutput, GesturePadFuser
from export import HTMLFormat, MDFormat

from typing import Tuple, List, Any
from time import sleep


class Backend:

    def __init__(self,
                 mediapipe_dir: str,
                 audio_path: str,
                 video_path: str,
                 mp_video_path: str,
                 gestures_dir: str,
                 gesture_prefix: str,
                 csv_path: str,
                 predictions_dir: str,
                 debug: bool = False):
        """
        Implements the back end of GesturePad, linking all modules together in the intended flow.
        :param mediapipe_dir: Path to the Google MediaPipe installation directory
        :param audio_path: Path to the audio file to write after recording
        :param video_path: Path to the video file to write after recording
        :param mp_video_path: Path to the video file to write after Google MediaPipe processing
        :param gestures_dir: Path to the directory wherein to store detected gestures
        :param gesture_prefix: Prefix in naming gesture files
        :param csv_path: Path to the CSV file to write for batch Google Cloud processing
        :param predictions_dir: Path to the directory wherein to store Google Cloud predictions (JSONL files)
        :param debug: Whether to print debug information and keep intermediate files for inspection (default: False)
        """

        if not os.path.exists(gestures_dir):
            raise FileNotFoundError("Invalid gesture directory.")
        elif not os.path.isdir(gestures_dir):
            raise NotADirectoryError("The path provided as gestures directory is not a directory.")
        elif not os.path.exists(predictions_dir):
            raise FileNotFoundError("Invalid predictions directory.")
        elif not os.path.isdir(predictions_dir):
            raise NotADirectoryError("The path provided as predictions directory is not a directory.")

        self.__debug = debug

        self.__mediapipe_dir = mediapipe_dir
        self.__audio_path = audio_path
        self.__video_path = video_path
        self.__mp_video_path = mp_video_path
        self.__gestures_dir = gestures_dir
        self.__gesture_prefix = gesture_prefix
        self.__csv_path = csv_path
        self.__predictions_dir = predictions_dir

        self.__mediapipe = MediaPipeHelper(mediapipe_dir=self.__mediapipe_dir)
        self.__gesture_client = GestureClient(csv_path=self.__csv_path, prediction_path=self.__predictions_dir)
        self.__speech_client = SpeechClient()

        # TODO: multimodal fusion
        # TODO: export to format

        # Internal state
        self.__recording = False
        self.__waiting_audio = False
        self.__waiting_gestures = False

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

        video_rec = Video(path=self.__video_path, fps=video_fps, resolution=video_resolution)
        video_rec.start()

        audio_rec = Audio(path=self.__audio_path)
        audio_rec.rec(max_audio_length)

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
                             length=audio_recorder.get_real_duration() * 1000,
                             bit_rate=16_000)

        # Align audio and video files
        delay = math.floor(v_input.length - a_input.length)
        audio_recorder.trim(int(delay))

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
                                               prev_gesture_threshold=0.0003,
                                               debug=self.__debug)

        stable_frames = gesture_identifier.process()
        frame_paths = []
        frame_timings = []
        for i, (frame, timing) in enumerate(stable_frames):
            path = os.path.join(self.__gestures_dir,
                                "{pref}{i}.jpeg".format(pref=self.__gesture_prefix, i=i))
            imageio.imwrite(path, frame)
            frame_paths.append(path)
            frame_timings.append(timing)

        return frame_paths, frame_timings

    def send_video(self, frame_paths: List[str]) -> Any:
        # TODO: not fully implemented, do not test yet
        """
        Sends a batch of images for image classification in an asynchronous fashion.
        :param frame_paths: List of paths to stable frame files to classify
        :return: google.longrunning.Operation object to later poll for response
        """

        operation = self.__gesture_client.process_images(image_paths=frame_paths)
        if not self.__debug:
            for path in frame_paths:
                try:
                    os.remove(path)
                except RuntimeError:
                    pass
            os.remove(self.__csv_path)

        return operation

    def send_audio(self, audio_input: AudioInput) -> Any:
        """
        Sends a file for word recognition in an asynchronous fashion.
        :param audio_input: AudioInput object representing the recorded audio
        :return: google.longrunning.Operation object to later poll for response
        """

        operation = self.__speech_client.process_audio(audio_path=audio_input.path)
        if not self.__debug:
            try:
                os.remove(audio_input.path)
            except RuntimeError:
                pass

        return operation

    def process_video_response(self):
        pass

    def process_audio_response(self):
        pass
    # --- --- ---

    # --- Multimodal fusion, formatting ---
    def parse_output(self):
        # TODO: wait for Google Cloud results
        # TODO: multimodal fusion
        pass

    def apply_format(self):
        # TODO: apply format
        pass
    # --- --- ---


if __name__ == '__main__':
    c, _ = read_config()

    b = Backend(mediapipe_dir=c["mediapipe_dir"],
                audio_path="../tmp/integration_audio.wav",
                video_path="../tmp/integration_video.mp4",
                mp_video_path="../tmp/integration_video_mp.mp4",
                gestures_dir="../tmp/integration_frames",
                gesture_prefix="image",
                csv_path="../tmp/integration_csv.csv",
                predictions_dir="../tmp/integration_results",
                debug=False)

    # Recording tests
    v, a = b.start_recording()
    sleep(15)
    v, a = b.stop_recording(v, a)
    # OK

    # Preprocessing tests
    frames, timings = b.preprocess_video(v)
    #print(len(frames), frames)
    #print(len(timings), timings)
    # OK
