"""
This file contains the SpeechClient definition.
"""

import os
from utils.config_helper import read_config
from rest_client import RESTClient, SimpleResponse


class SpeechClient:

    def __init__(self):
        # Let Google Cloud libraries pick up credentials from environment variables
        config, _ = read_config()
        os.environ["PROJECT_ID"] = config["project_id"]
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config["credentials"]
        pass


if __name__ == '__main__':
    c = SpeechClient()
    print(os.environ["PROJECT_ID"])
