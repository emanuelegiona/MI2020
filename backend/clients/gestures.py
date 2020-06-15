"""
This file contains the GestureClient definition.
"""

import os
from utils.config_helper import read_config
from rest_client import RESTClient, SimpleResponse


class GestureClient:

    def __init__(self):
        # Let Google Cloud libraries pick up credentials from environment variables
        config, _ = read_config()
        os.environ["PROJECT_ID"] = config["project_id"]
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config["credentials"]
        pass


if __name__ == '__main__':
    c = GestureClient()
    print(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
