"""
This file contains the SpeechClient definition.
"""

import os
from utils.config_helper import read_config
from google.cloud import speech_v1
from typing import Any, List, Union, Tuple


class SpeechClient:

    def __init__(self, language: str = "en-US"):
        """
        Wrapper class for asynchronous, timestamp-enabled word recognition with Google Cloud Speech.
        :param language: Language used in the audio file (default: 'en-US')
        """

        # Let Google Cloud libraries pick up credentials from environment variables
        config, _ = read_config()
        os.environ["PROJECT_ID"] = config["project_id"]
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config["credentials"]

        self.__gspeech_client = speech_v1.SpeechClient()
        self.__speech_config = {"model": "default",  # 'default' model is optimized for long-form audio or dictation
                                "enable_word_time_offsets": True,
                                "language_code": language}

    def process_audio(self, audio_path: str) -> Any:
        """
        Sends a file for word recognition in an asynchronous fashion.
        :param audio_path: Path to the audio file to process
        :return: google.longrunning.Operation object to later poll for response
        :raises FileNotFoundError, ValueError for invalid audio files
        """

        if not os.path.exists(audio_path):
            raise FileNotFoundError("Invalid audio file.")
        elif not os.path.isfile(audio_path):
            raise ValueError("The provided path is not a regular file.")

        with open(audio_path, "rb") as audio_file:
            audio_content = audio_file.read()
        audio = {"content": audio_content}
        operation = self.__gspeech_client.long_running_recognize(config=self.__speech_config, audio=audio)

        return operation

    @staticmethod
    def get_words(operation: Any,
                  whole_transcript: bool = False
                  ) -> Union[List[Tuple[str, float, float]], Tuple[str, List[Tuple[str, float, float]]]]:
        """
        Waits for the list of recognized words given the Operation object previously obtained from a process_audio
        request.
        :param operation: google.longrunning.Operation object to wait completion for
        :param whole_transcript: Additionally returns a single string containing the whole transcript (default: False)
        :return: whole_transcript = False:
                    - List containing Tuples (word: str, start_time: float, end_time: float)
                 whole_transcript = True:
                    - Tuple containing at positions:
                        - 0: String representing the whole transcript
                        - 1: List containing Tuples (word: str, start_time: float, end_time: float)
        """

        response = operation.result()
        response = response.results[0].alternatives[0]
        words = []
        for utterance in response.words:
            word = str(utterance.word)
            start_time = float(utterance.start_time.seconds)
            start_time += float(utterance.start_time.nanos) / 10e9
            end_time = float(utterance.end_time.seconds)
            end_time += float(utterance.end_time.nanos) / 10e9
            words.append((word, start_time, end_time))

        if whole_transcript:
            return str(response.transcript), words
        return words


if __name__ == '__main__':
    c = SpeechClient()
    audio_file = "../../tmp/audio.wav"
    o = c.process_audio(audio_file)
    w_list = c.get_words(o)
    for w, start, end in w_list:
        print(f"{w} (start: {start}, end: {end})")
