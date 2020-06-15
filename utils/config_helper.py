"""
This file is meant to be executed as part of the Makefile to automate parts of GesturePad configuration.
"""

import os
import argparse
import json
from typing import Dict


def main(arguments: argparse.Namespace) -> None:
    """
    Processes various configuration options.
    :param arguments: argparse.Namespace containing the currently selected options and their values
    :return: None
    """

    # Locate config.json file
    config_json, config_file_path = read_config()

    # Set Google MediaPipe installation directory
    if arguments.parent_dir is not None:
        set_mediapipe_dir(config_json, os.path.join(arguments.parent_dir, "mediapipe"))

    # Set Google Cloud Platform credentials file
    if arguments.credentials is not None:
        set_credentials_path(config_json, arguments.credentials)

    with open(config_file_path, "w") as config_file:
        json.dump(config_json, config_file)
    print("Configuration complete.")


def read_config() -> (Dict[str, str], str):
    """
    Resolves the config.json path w.r.t. parent_dir (if any), and reads the file.
    :return: Tuple containing: JSON contents as Dict; path to the config.json file
    """

    wd = os.getcwd()
    config_filename = "config.json"

    if "MI2020" not in wd:
        if "MI2020" not in os.listdir(wd):
            raise RuntimeError("Current working directory is not the parent directory to 'MI2020'")
        else:
            wd = os.path.join(wd, "MI2020")
    else:
        wd = wd[:wd.find("/MI2020")+7]
    config_file_path = os.path.join(wd, "data", config_filename)

    with open(config_file_path) as config_file:
        config_json = json.load(config_file)

    return config_json, config_file_path


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


def set_credentials_path(configuration: Dict[str, str], credentials_path: str) -> None:
    """
    Configures Google Cloud Platform credentials file.
    :param configuration: Configuration for GesturePad (JSON represented in data/config.json)
    :param credentials_path: Absolute path to the Google Cloud Platform credentials file
    :return: None
    :raises FileNotFoundError, ValueError, or NotADirectoryError for invalid MediaPipe directory
    """

    print("Configuring Google Cloud Platform credentials file...")
    if not os.path.exists(credentials_path):
        raise FileNotFoundError("Invalid credentials file.")
    elif not os.path.isabs(credentials_path):
        raise ValueError("An absolute path must be provided.")
    elif not os.path.isfile(credentials_path):
        raise ValueError("The provided path is not a regular file.")
    configuration["credentials"] = credentials_path
    print("Done.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser("GesturePad configuration helper.")
    parser.add_argument("--parent_dir", type=str,
                        help="Absolute path to the parent directory of MI2020 and Google MediaPipe")
    parser.add_argument("--credentials", type=str,
                        help="Absolute path to the Google Cloud Platform credentials file")
    args = parser.parse_args()
    main(args)
