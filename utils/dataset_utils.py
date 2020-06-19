"""
This file is meant to be executed as part of the Makefile to automate parts of GesturePad configuration.
"""

import os
import argparse
import shutil
from random import randint
from typing import Dict


def main(arguments: argparse.Namespace) -> None:
    """
    Processes various configuration options.
    :param arguments: argparse.Namespace containing the currently selected options and their values
    :return: None
    :raises FileNotFoundError, ValueError for invalid dataset directory paths
    """

    path = arguments.dataset_path
    number = arguments.target_number

    if not os.path.exists(path):
        raise FileNotFoundError("Invalid credentials file.")
    elif not os.path.isdir(path):
        raise ValueError("The provided path is not a regular file.")

    examples = rename_files(dataset_path=path)
    if number is not None:
        augment(dataset_path=path, examples_per_gesture=examples, target_number=number)


def rename_files(dataset_path: str) -> Dict[str, int]:
    """
    Assigns unique names to files using the name of their parent directory.
    :param dataset_path: Path to the dataset directory
    :return: Dictionary mapping gestures to the number of examples
    """

    examples_per_gesture = {}
    for gesture in os.listdir(dataset_path):
        curr_gesture_name = os.path.basename(gesture)
        examples_per_gesture[curr_gesture_name] = 0

        for i, image in enumerate(os.listdir(os.path.join(dataset_path, gesture))):
            i += 1
            curr_image = os.path.join(dataset_path,
                                      gesture,
                                      os.path.basename(image))
            target_image = os.path.join(dataset_path,
                                        gesture,
                                        "{gesture}{i}.jpeg".format(gesture=str.lower(curr_gesture_name), i=i))

            os.rename(curr_image, target_image)
            examples_per_gesture[curr_gesture_name] = i

    return examples_per_gesture


def augment(dataset_path: str, examples_per_gesture: Dict[str, int], target_number: int) -> None:
    """
    Randomly selects images and applies small variations to them, until each gesture reaches the given number of examples.
    :param dataset_path: Path to the dataset directory
    :param examples_per_gesture: Dictionary mapping gestures to the number of examples
    :param target_number: Desired number of examples for each gesture
    :return: None
    """

    for gesture in os.listdir(dataset_path):
        curr_gesture_name = os.path.basename(gesture)
        example_number = examples_per_gesture[curr_gesture_name]
        artificial = 0
        while example_number + artificial < target_number:
            i = randint(1, example_number)
            curr_image = os.path.join(dataset_path,
                                      gesture,
                                      "{gesture}{i}.jpeg".format(gesture=str.lower(curr_gesture_name), i=i))
            artificial += 1
            target_image = os.path.join(dataset_path,
                                        gesture,
                                        "{gesture}{i}.jpeg".format(gesture=str.lower(curr_gesture_name),
                                                                   i=(example_number + artificial)))

            shutil.copy(curr_image, target_image)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Dataset utils.")
    parser.add_argument("dataset_path", type=str,
                        help="Path to the dataset directory")
    parser.add_argument("--target_number", type=int,
                        help="Desired number of examples for each gesture")
    args = parser.parse_args()
    main(args)
