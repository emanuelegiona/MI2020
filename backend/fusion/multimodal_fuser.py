"""
This file contains all the necessary code to fuse recognized words and gestures based on their timestamps.
"""

from abc import ABC
from typing import List
from clients.gestures import Gesture, GESTURE_PAIR
from multimodal_types import WordOutput, GestureOutput, ModalityOutput


class MultimodalFuser:

    def __init__(self, sync_tolerance: float = 0):
        """
        General multimodal utterance fuser.
        :param sync_tolerance: Tolerance to allow during synchronization (in seconds)
        """

        if sync_tolerance < 0:
            raise ValueError("Synchronization tolerance cannot be less than 0.")

        self.sync_tolerance = sync_tolerance

    def fuse(self, *args: List[ModalityOutput]) -> List[ModalityOutput]:
        """
        Fuses several modalities utterances into a single multimodal stream.
        :param args: Variable number of Lists containing utterances for each modality
        :return: List containing ordered (synchronized) utterances from multiple modalities
        """

        raise NotImplementedError()


class GesturePadFuser(MultimodalFuser, ABC):

    def __init__(self, sync_tolerance: float = 0):
        """
        MultimodalFuser implementation for GesturePad, fusing recognized words and gestures.
        :param sync_tolerance: Tolerance to allow during synchronization (in seconds)
        """

        super(GesturePadFuser, self).__init__(sync_tolerance)

    def fuse(self, *args: List[ModalityOutput]) -> List[ModalityOutput]:
        """
        Fuses audio and video modalities tokens, providing a single ordering among words and gestures.
        :param args: Mandatory Lists for recognized words and gestures
        :return: List containing ordered words and gestures
        """

        if len(args) != 2:
            raise ValueError("Both recognized words and gestures must be provided.")

        words = args[0]
        gestures = args[1]

        if words is None or len(words) == 0:
            raise ValueError("List of recognized words cannot be empty.")

        if gestures is None or len(gestures) == 0:
            return words

        def next_output(tokens: List[ModalityOutput]):
            curr = tokens[0] if (tokens is not None and len(tokens) > 0) else None
            tokens = tokens[1:]
            return curr, tokens

        multimodal_output = []
        gesture_queue = []
        gesture, gestures = next_output(gestures)
        word, words = next_output(words)
        while True:
            # Exhaust the remaining gestures
            if word is None:
                while gesture is not None:
                    # Handle gestures that work in pairs in a queue
                    if gesture.utterance in GESTURE_PAIR:
                        if len(gesture_queue) > 0 and gesture_queue[-1].utterance == gesture.utterance:
                            gesture_queue = gesture_queue[:-1]
                        else:
                            gesture_queue.append(gesture)

                    multimodal_output.append(gesture)
                    gesture, gestures = next_output(gestures)

                # Close the gestures that work in pairs that have been left open
                while len(gesture_queue) > 0:
                    multimodal_output.append(gesture_queue[-1])
                    gesture_queue = gesture_queue[:-1]

            # Exhaust the remaining words
            if gesture is None:
                while word is not None:
                    multimodal_output.append(word)
                    word, words = next_output(words)

            # Intermediate steps
            if gesture is not None and word is not None:
                # Current gesture can be added TODO: making it % w.r.t. word length (word.end - word.start)?
                if gesture.timing <= word.timing + self.sync_tolerance:
                    # Handle gestures that work in pairs in a queue
                    if gesture.utterance in GESTURE_PAIR:
                        if len(gesture_queue) > 0 and gesture_queue[-1].utterance == gesture.utterance:
                            gesture_queue = gesture_queue[:-1]
                        else:
                            gesture_queue.append(gesture)

                    multimodal_output.append(gesture)
                    gesture, gestures = next_output(gestures)

                # Exhaust all the words that are between the current gesture and the next one
                while word is not None and word.timing < gesture.timing:
                    multimodal_output.append(word)
                    word, words = next_output(words)

            # Exit condition
            if gesture is None and word is None:
                break

        return multimodal_output


if __name__ == '__main__':
    w = [WordOutput("this", 1, 3),
         WordOutput("is", 5, 7),
         WordOutput("a", 9, 11),
         WordOutput("test", 13, 15),
         WordOutput("for", 17, 19),
         WordOutput("Google", 21, 23),
         WordOutput("Cloud", 25, 27)]

    g = [GestureOutput(Gesture.ITALICS, 1.5),
         #GestureOutput(Gesture.ITALICS, 2),
         GestureOutput(Gesture.COMMA, 14),
         GestureOutput(Gesture.BOLD, 20),
         #GestureOutput(Gesture.BOLD, 30),
         GestureOutput(Gesture.EXCLAMATION_MARK, 35),
         GestureOutput(Gesture.EXCLAMATION_MARK, 40),
         GestureOutput(Gesture.EXCLAMATION_MARK, 50),
         GestureOutput(Gesture.EXCLAMATION_MARK, 50),
         GestureOutput(Gesture.EXCLAMATION_MARK, 50)]

    f = GesturePadFuser(sync_tolerance=0.5)
    final = f.fuse(w, g)

    final = [*map(lambda x: x.utterance, final)]
    print(final)
