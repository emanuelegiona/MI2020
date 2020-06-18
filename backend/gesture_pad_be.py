"""
This file contains the code running in the back end of GesturePad.
"""

import os
import imageio
import math

#from utils.config_helper import read_config
from recording import Audio, Video
from mediapipe import MediaPipeHelper, GestureIdentifier
from clients import SpeechClient, GestureClient
from fusion import AudioInput, WordOutput, VideoInput, GestureOutput, GesturePadFuser
from export import HTMLFormat, MDFormat

from typing import Tuple
from time import sleep


class Backend:

    def __init__(self,
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
        :param audio_path: Path to the audio file to write after recording
        :param video_path: Path to the video file to write after recording
        :param mp_video_path: Path to the video file to write after Google MediaPipe processing
        :param gestures_dir: Path to the directory wherein to store detected gestures
        :param gesture_prefix: Prefix in naming gesture files
        :param csv_path: Path to the CSV file to write for batch Google Cloud processing
        :param predictions_dir: Path to the directory wherein to store Google Cloud predictions (JSONL files)
        :param debug: Whether to print debug information and keep intermediate files for inspection (default: False)
        """

        # TODO: sanity check on paths
        self.__debug = debug

        self.__audio_path = audio_path
        self.__video_path = video_path
        self.__mp_video_path = mp_video_path
        self.__gestures_dir = gestures_dir
        self.__gesture_prefix = gesture_prefix
        self.__csv_path = csv_path
        self.__predictions_dir = predictions_dir

        # TODO: MediaPipe helper
        # TODO: gesture identifier
        # TODO: Google Cloud clients
        # TODO: multimodal fusion
        # TODO: export to format

        # Internal state
        self.__recording = False

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
    def preprocess_video(self, video_input: VideoInput):
        # TODO: MediaPipe
        # TODO: gesture identifier
        pass

    def send_video(self):
        # TODO: Google Cloud async processing
        pass

    def send_audio(self):
        # TODO: Google Cloud async processing
        pass

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
    b = Backend(audio_path="../tmp/integration_audio.wav",
                video_path="../tmp/integration_video.mp4",
                mp_video_path="../tmp/integration_video_mp.mp4",
                gestures_dir="../tmp/integration_frames",
                gesture_prefix="image",
                csv_path="../tmp/integration_csv.csv",
                predictions_dir="../tmp/integration_results",
                debug=False)

    v, a = b.start_recording()
    sleep(15)
    v, a = b.stop_recording(v, a)
    print(v)
    print(a)
