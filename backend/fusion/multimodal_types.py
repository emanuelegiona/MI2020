"""
This file contains definitions for modality types, their inputs and outputs.
"""

import os
from copy import deepcopy
from typing import Tuple, Optional, Any, Dict
from backend.clients.gestures import Gesture


class ModalityInput:

    def __init__(self, path: Optional[str] = None, length: Optional[float] = None):
        """
        Abstraction for a general input token from a modality.
        :param path: Path to the input token file
        :param length: Duration of the input token (in seconds)
        :raises FileNotFoundError, ValueError for invalid paths or length values
        """

        if not os.path.exists(path):
            raise FileNotFoundError("Invalid input file.")
        elif not os.path.isfile(path):
            raise ValueError("The provided path is not a regular file.")
        elif length is not None and length <= 0:
            raise ValueError("The file cannot have a duration less than 0.")

        self.path = path
        self.length = length


class AudioInput(ModalityInput):

    def __init__(self, path: Optional[str] = None, length: Optional[float] = None, bit_rate: Optional[float] = None):
        """
        Audio input token.
        :param path: Path to the input token file
        :param length: Duration of the audio input token (in seconds)
        :param bit_rate: Bit rate of the recording (ni Hertz)
        :raises ValueError for invalid bit rate values (also see: ModalityInput)
        """

        if bit_rate is not None and bit_rate <= 0:
            raise ValueError("The file cannot have a bit rate less than 0.")

        super().__init__(path, length)
        self.bit_rate = bit_rate


class VideoInput(ModalityInput):

    def __init__(self,
                 path: Optional[str] = None,
                 length: Optional[float] = None,
                 fps: Optional[float] = None,
                 resolution: Optional[Tuple[int, int]] = None):
        """
        Video input token.
        :param path: Path to the input token file
        :param length: Duration of the video input token (in seconds)
        :param fps: Frames per second of the recording
        :param resolution: Resolution of frames in the recording (as tuples in the format width x height)
        :raises ValueError for invalid FPS and resolution values (also see: ModalityInput)
        """

        if fps is not None and fps <= 0:
            raise ValueError("The file cannot have less than 0 FPS.")
        elif resolution is not None and (resolution[0] == 0 or resolution[1] == 0):
            raise ValueError("The file cannot have a resolution wherein a side is equal to 0.")

        super(VideoInput, self).__init__(path, length)
        self.fps = fps
        self.resolution = resolution


class ModalityOutput:

    def __init__(self,
                 utterance: Optional[Any] = None,
                 timing: Optional[float] = None,
                 params: Optional[Dict[Any, Any]] = None):
        """
        Abstraction for a general output token from a modality.
        :param utterance: Recognized utterance that carries semantic information
        :param timing: Timestamp associated with the utterance (in seconds)
        :param params: Dictionary containing more information regarding the utterance (Optional)
        :raises ValueError for invalid combinations of values for utterance and timing
        """

        if utterance is not None and timing is None:
            raise ValueError("Utterance and timing must be both defined if any of the two is defined.")
        elif utterance is None and timing is not None:
            raise ValueError("Utterances and timings must be both defined if any of the two is defined.")
        elif timing is not None and timing < 0:
            raise ValueError("Timing cannot be less than 0.")

        self.utterance = deepcopy(utterance)
        self.timing = timing
        self.params = deepcopy(params)


class WordOutput(ModalityOutput):

    def __init__(self,
                 word: Optional[str] = None,
                 timing: Optional[float] = None,
                 end_timing: Optional[float] = None):
        """
        Recognized word from an audio input token.
        :param word: Recognized word
        :param timing: Timestamp associated with the start of the recognition
        :param end_timing: Timestamp associated with the end of the recognition
        :raises ValueError for invalid end_timing values w.r.t. timing value (also see: ModalityOutput)
        """

        if end_timing is not None and end_timing < timing:
            raise ValueError("End time cannot precede recognition time.")

        super(WordOutput, self).__init__(word, timing)
        self.params = {"end_time": end_timing}


class GestureOutput(ModalityOutput):

    def __init__(self,
                 gesture: Optional[Gesture] = None,
                 timing: Optional[float] = None,
                 confidence: Optional[float] = None):
        """
        Recognized gesture from a video input token.
        :param gesture: Recognized gesture
        :param timing: Timestamp associated with the start of recognition
        :param confidence: Confidence in the gesture recognition
        :raises ValueError for invalid confidence values
        """

        if confidence is not None and not (0 <= confidence <= 1):
            raise ValueError("Confidence must be within the range [0,1].")

        super(GestureOutput, self).__init__(gesture, timing)
        self.params = {"confidence": confidence}
