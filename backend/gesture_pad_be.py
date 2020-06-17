"""
This file contains the code running in the back end of GesturePad.
"""

from utils.config_helper import read_config
from recording import Audio, Video
from mediapipe import MediaPipeHelper, GestureIdentifier
from clients import SpeechClient, GestureClient
from fusion import AudioInput, WordOutput, VideoInput, GestureOutput, GesturePadFuser
from export import HTMLFormat, MDFormat


class Backend:

    def __init__(self):
        # TODO: audio recording client
        # TODO: video recording client
        # TODO: MediaPipe helper
        # TODO: gesture identifier
        # TODO: Google Cloud clients
        # TODO: multimodal fusion
        # TODO: export to format
        pass

    def record_input(self):
        # TODO: record audio & video
        pass

    def preprocess_video(self):
        # TODO: MediaPipe
        # TODO: gesture identifier
        pass

    def process_input(self):
        # TODO: Google Cloud async processing
        pass

    def parse_output(self):
        # TODO: wait for Google Cloud results
        # TODO: multimodal fusion
        pass

    def apply_format(self):
        # TODO: apply format
        pass


if __name__ == '__main__':
    pass
