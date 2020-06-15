"""
This file contains the GestureClient definition.
"""

import os
from utils.config_helper import read_config
from google.cloud import automl, storage
from typing import List, Any


class GestureClient:

    def __init__(self, csv_path: str, prediction_path: str, prediction_threshold: float = 0.8):
        """
        Wrapper class for asynchronous, batch-oriented image classification with Google Vision AutoML.
        :param csv_path: Path to the CSV file to create for each batch of predictions
        :param prediction_path: Path to the directory wherein store JSONL files containing predictions
        :param prediction_threshold: Score threshold for predictions (default: 0.8)
        :raises ValueError for invalid prediction_threshold values
        """

        if not (0 <= prediction_threshold <= 1):
            raise ValueError("Prediction threshold must be within the range [0,1].")
        elif not os.path.exists(prediction_path):
            raise FileNotFoundError("Invalid prediction directory.")
        elif not os.path.isdir(prediction_path):
            raise NotADirectoryError("The provided path is not a directory.")

        # Let Google Cloud libraries pick up credentials from environment variables
        config, _ = read_config()
        os.environ["PROJECT_ID"] = config["project_id"]
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config["credentials"]

        self.__csv_path = csv_path
        self.__prediction_path = prediction_path
        self.__prediction_threshold = prediction_threshold

        # Google Cloud Storage
        self.__gcs_client = storage.Client()
        self.__input_bucket_name = config["input_bucket_name"]
        self.__output_bucket_name = config["output_bucket_name"]
        self.__input_bucket = self.__gcs_client.get_bucket(self.__input_bucket_name)
        self.__output_bucket = self.__gcs_client.get_bucket(self.__output_bucket_name)

        # Google Cloud Vision AutoML TODO: MUST BE TESTED after AutoML deployment
        #self.__gvision_client = automl.PredictionServiceClient()
        #self.__full_model_id = self.__gvision_client.model_path(project=config["project_id"],
        #                                                        location=config["location"],
        #                                                        model=config["model_id"])

    def process_images(self, image_paths: List[str]) -> Any:
        """
        Sends a batch of images for image classification in an asynchronous fashion.
        :param image_paths: List of paths to images to classify
        :return: google.longrunning.Operation object to later poll for response
        """

        # Upload to Google Cloud Storage TODO: test ok
        remote_urls = []
        for i, path in enumerate(image_paths):
            if (not os.path.exists(path)) or (not os.path.isfile(path)):
                continue

            image_id = f"image{i}.jpeg"
            blob = self.__input_bucket.blob(image_id)
            blob.upload_from_filename(path)
            remote_urls.append("gs://{bucket}/{object}".format(bucket=self.__input_bucket_name,
                                                               object=image_id))

        # TODO: remaining part of method MUST BE TESTED after AutoML deployment
        remote_urls = []
        if len(remote_urls) == 0:
            raise RuntimeError("No image has been uploaded to Google Cloud Storage.")

        # Batch prediction request to Google Cloud Vision AutoML
        with open(self.__csv_path, "w") as csv_file:
            for url in remote_urls:
                csv_file.write(f"{url}\n")
        blob = self.__input_bucket.blob("batch.csv")
        blob.upload_from_filename(self.__csv_path)

        batch_input_config = {"gcs_source": "gs://{bucket}/{object}".format(bucket=self.__input_bucket_name,
                                                                            object="batch.csv")}
        batch_output_config = {"gcs_destination": "gs://{bucket}".format(bucket=self.__output_bucket_name)}
        params = {"score_threshold": str(self.__prediction_threshold)}
        operation = self.__gvision_client.batch_predict(name=self.__full_model_id,
                                                        input_config=batch_input_config,
                                                        output_config=batch_output_config,
                                                        params=params)

        return operation

    def get_gestures(self, operation: Any, prefix: str = "prediction") -> List[str]:
        """
        Waits for the labels associated to images due to a previously obtained Operation object through a process_images
        request.
        :param operation: google.longrunning.Operation object to wait completion for
        :param prefix: Prefix to apply when iterating over contents of a bucket
        :return: List of labels associated to images, consistent with the original ordering at process_images
        """

        # Enforce waiting for results, if necessary
        #response = operation.result()

        # Download predictions TODO: test ok
        all_blobs = self.__output_bucket.list_blobs(prefix=prefix)
        dir_position = 0
        for i, blob in enumerate(all_blobs):
            pure_name = blob.name
            pure_name = pure_name[::-1]
            stop = pure_name.find("/")
            pure_name = pure_name[:stop]
            pure_name = pure_name[::-1]

            if len(pure_name) > 0:
                blob.download_to_filename(os.path.join(self.__prediction_path, pure_name))
            else:
                dir_position = i

        # Avoid possible errors by positioning the "directory" as last blob
        all_blobs.append(all_blobs.pop(dir_position))
        self.__output_bucket.delete_blobs(all_blobs)

        # TODO: associate predicted label with each original image; sort by ascending image id
        # TODO: internal JSONL prediction file analysis MUST BE DEVELOPED after AutoML deployment

        return []


if __name__ == '__main__':
    c = GestureClient(csv_path="../../tmp/batch.csv", prediction_path="../../tmp/gcs_test")
    #c.process_images(["../../tmp/frame_test/gesture_3.000.jpg",
    #                  "../../tmp/frame_test/gesture_7.500.jpg"])
    c.get_gestures(None)
