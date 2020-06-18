"""
This file contains all the necessary code to 'translate' a ModalityOutput utterance into a specific formatting.
E.g. 'Gesture.BOLD' is interpreted either as '<b>' or '</b>' for HTML documents, while in Markdown '**' is used.
"""

from backend.clients.gestures import Gesture, GESTURE_PAIR
from typing import Optional


class Format:

    def __init__(self):
        """
        Abstraction behind any text format.
        """

        self.mapping = {Gesture.NO_GESTURE: None,
                        Gesture.COMMA: ",",
                        Gesture.FULL_STOP: ".",
                        Gesture.COLON: ":",
                        Gesture.SEMICOLON: ";",
                        Gesture.EXCLAMATION_MARK: "!",
                        Gesture.QUESTION_MARK: "?",
                        Gesture.NEW_LINE: "\n"}

    def __call__(self, gesture: Gesture) -> Optional[str]:
        """
        Use the formatting rules for this format to translate the given gesture.
        :param gesture: Gesture to translate
        :return: String associated with the given gesture or None if no mapping has been defined
        """

        return self.mapping.get(gesture, None)


class HTMLFormat(Format):

    def __init__(self):
        """
        HTML formatting for defined gestures.
        """

        super(HTMLFormat, self).__init__()
        self.mapping[Gesture.BOLD] = "<b>"
        self.mapping[Gesture.ITALICS] = "<i>"
        self.mapping[Gesture.UNDERLINED] = "<u>"
        self.mapping[Gesture.NEW_LINE] = "<br>"

    def __call__(self, gesture: Gesture, close: bool = False) -> str:
        """
        Use the formatting rules for HTML to translate the given gesture.
        :param gesture: Gesture to translate
        :param close: For tags that work in pairs, returns the closing tag (default: False)
        :return: String associated with the given gesture or None if no mapping has been defined
        """

        str_version = super().__call__(gesture)
        if close and gesture in GESTURE_PAIR and gesture in self.mapping:
            str_version = str_version.replace("<", "</")
        return str_version


class MDFormat(Format):

    def __init__(self):
        """
        Markdown formatting for defined gestures.
        """

        super(MDFormat, self).__init__()
        self.mapping[Gesture.BOLD] = "**"
        self.mapping[Gesture.ITALICS] = "*"
        self.mapping[Gesture.NEW_LINE] = "\n\n"


if __name__ == '__main__':
    f = MDFormat()
    print(f(Gesture.BOLD))
    print(f(Gesture.UNDERLINED))
