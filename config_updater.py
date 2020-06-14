"""
This file is meant to be executed as part of the Makefile to automate parts of GesturePad configuration.
"""

import os
import argparse
import json
from typing import Dict


def set_mediapipe_dir(configuration: Dict[str, str], mediapipe_dir: str) -> None:
    """
    Configures Google MediaPipe installation directory.
    :param configuration: Configuration for GesturePad (JSON represented in data/config.json)
    :param mediapipe_dir: Absolute path to Google MediaPipe installation directory
    :return: None
    :raises FileNotFoundError, ValueError, or NotADirectoryError for invalid MediaPipe directory
    """

    print("Configuring MediaPipe installation directory...")
    if not os.path.exists(mediapipe_dir):
        raise FileNotFoundError("Invalid MediaPipe installation directory.")
    elif not os.path.isabs(mediapipe_dir):
        raise ValueError("An absolute path must be provided.")
    elif not os.path.isdir(mediapipe_dir):
        raise NotADirectoryError("The provided path is not a directory.")
    configuration["mediapipe_dir"] = mediapipe_dir
    print("Done.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser("GesturePad configuration helper.")
    parser.add_argument("parent_dir", type=str,
                        help="Absolute path to the parent directory of MI2020 and Google MediaPipe")
    args = parser.parse_args()

    config_file_path = "data/config.json"
    config_file_path = os.path.join(args.parent_dir, "MI2020", config_file_path)

    with open(config_file_path) as config_file:
        config_json = json.load(config_file)

    set_mediapipe_dir(config_json, os.path.join(args.parent_dir, "mediapipe"))

    with open(config_file_path, "w") as config_file:
        json.dump(config_json, config_file)
    print("Configuration complete.")
