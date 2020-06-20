"""
This file contains the GestureClient definition.
"""

import os
from utils.config_helper import read_config
from google.cloud import automl
from typing import List
from enum import Enum, auto


class Gesture(Enum):
    """
    Enumerator to identify which gesture has been detected.
    """

    NO_GESTURE = auto()

    # Emphasis
    BOLD = auto()
    ITALICS = auto()
    UNDERLINED = auto()

    # Punctuation
    COMMA = auto()
    FULL_STOP = auto()
    COLON = auto()
    SEMICOLON = auto()
    EXCLAMATION_MARK = auto()
    QUESTION_MARK = auto()

    # Other
    CAPS_LOCK = auto()
    NEW_LINE = auto()


GESTURE_PAIR = {Gesture.BOLD,
                Gesture.ITALICS,
                Gesture.UNDERLINED,
                Gesture.CAPS_LOCK}

GESTURE_LOOKUP = {"NO_GESTURE": Gesture.NO_GESTURE,
                  "BOLD": Gesture.BOLD,
                  "ITALICS": Gesture.ITALICS,
                  "UNDERLINED": Gesture.UNDERLINED,
                  "COMMA": Gesture.COMMA,
                  "FULL_STOP": Gesture.FULL_STOP,
                  "SEMICOLON": Gesture.SEMICOLON,
                  "COLON": Gesture.COLON,
                  "EXCLAMATION_MARK": Gesture.EXCLAMATION_MARK,
                  "QUESTION_MARK": Gesture.QUESTION_MARK,
                  "CAPS_LOCK": Gesture.CAPS_LOCK,
                  "NEW_LINE": Gesture.NEW_LINE}


class GestureClient:

    def __init__(self, prediction_threshold: float = 0.8):
        """
        Wrapper class for asynchronous, batch-oriented image classification with Google Vision AutoML.
        :param prediction_threshold: Score threshold for predictions (default: 0.8)
        :raises ValueError for invalid prediction_threshold values
        """

        if not (0 <= prediction_threshold <= 1):
            raise ValueError("Prediction threshold must be within the range [0,1].")

        # Let Google Cloud libraries pick up credentials from environment variables
        config, _ = read_config()
        os.environ["PROJECT_ID"] = config["project_id"]
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config["credentials"]

        # Google Cloud Vision AutoML
        self.__gvision_client = automl.PredictionServiceClient()
        self.__full_model_id = self.__gvision_client.model_path(project=config["project_id"],
                                                                location=config["location"],
                                                                model=config["model_id"])
        self.__prediction_threshold = prediction_threshold

    def process_images(self, image_paths: List[str]) -> List[Gesture]:
        """
        Sends a batch of images for image classification in a synchronous fashion.
        :param image_paths: List of paths to images to classify
        :return: List of Gesture associated to images, consistent with the original ordering provided at process_images
        """

        recognized_gestures = {}
        for path in image_paths:
            if (not os.path.exists(path)) or (not os.path.isfile(path)):
                recognized_gestures[path] = Gesture.NO_GESTURE
                continue

            with open(path, "rb") as image_file:
                image_content = image_file.read()

            payload = automl.types.ExamplePayload(image=automl.types.Image(image_bytes=image_content))
            params = {"score_threshold": str(self.__prediction_threshold)}
            response = self.__gvision_client.predict(name=self.__full_model_id,
                                                     payload=payload,
                                                     params=params)

            for result in response.payload:
                recognized_gestures[path] = GESTURE_LOOKUP.get(result.display_name, Gesture.NO_GESTURE)

        adjusted_gestures = [recognized_gestures.get(path, Gesture.NO_GESTURE) for path in image_paths]

        return adjusted_gestures


if __name__ == '__main__':
    c = GestureClient()
    gestures = c.process_images(["../../tmp/frame_test/frame1.jpeg",
                                 "../../tmp/frame_test/frame2.jpeg"])
    print(gestures)
