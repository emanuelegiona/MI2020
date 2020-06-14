"""
This file contains all the necessary code to detect stable gestures in a Google MediaPipe-produced video.
"""

import os
import numpy as np
import imageio

from typing import List, Tuple, Optional


class GestureIdentifier:

    def __init__(self, video_path: str, stable_frames: int = 3, stability: float = 2.5, gesture_interval: int = 1):
        # TODO: add white % threshold for __check_stability()
        """
        Processes a MediaPipe-produced video to detect gestures in it.
        :param video_path: Path to the video to analyze
        :param stable_frames: Number of frames required to detect a gesture
        :param stability: Stability threshold (1 = exact same frame)
        :param gesture_interval: Number of frames to skip between gestures
        :raises FileNotFoundError, ValueError for invalid video file path
        """

        if not os.path.exists(video_path):
            raise FileNotFoundError("No video file found.")
        elif not os.path.isfile(video_path):
            raise ValueError("The provided path is not a regular file.")

        self.__video_path = video_path
        self.__stable_frames = stable_frames
        self.__stability = stability
        self.__gesture_interval = gesture_interval

        reader = imageio.get_reader(video_path)
        metadata = reader.get_meta_data()
        self.__total_frames = len([*enumerate(reader)])
        self.__fps = metadata["fps"]
        self.__duration = metadata["duration"]

    @staticmethod
    def __enhance_frame(frame: imageio.core.Image) -> imageio.core.Image:
        """
        Enhances the outline of landmarks in a frame, making all the rest white.
        :param frame: A frame from a MediaPipe-produced video
        :return: The given frame with yellow landmarks and all the rest being white
        """

        array = imageio.core.asarray(frame)
        mask_red = np.not_equal(array, (255, 0, 0))
        mask_green = np.not_equal(array, (0, 255, 0))
        mask = mask_red | mask_green
        array[mask] = 255

        return imageio.core.Image(array)

    def __compute_seconds(self, index: int) -> float:
        """
        Given the frame number, computes the timestamp of occurrence in seconds.
        :param index: Number of frame
        :return: Timestamp of occurrence in seconds
        """
        return float(index)/self.__total_frames * self.__duration

    def __check_stability(self, frame_buffer: List[imageio.core.Image]) -> (bool, Optional[imageio.core.Image]):
        # TODO: threshold on white % to avoid stable frames with no gesture being recognized as such
        # Compute the mean frame of the buffer
        frame_buffer = [*map(imageio.core.asarray, frame_buffer)]
        frame_buffer = [*map(lambda x: x.astype(np.float32), frame_buffer)]
        frame_buffer = [*map(lambda x: np.average(x, axis=-1), frame_buffer)]
        frame_buffer = [*map(lambda x: (x - x.min())*255/(x.max() - x.min()), frame_buffer)]
        mean_frame = sum(frame_buffer) / len(frame_buffer)

        # Check if the average L1 norm is within threshold
        l1 = [*map(lambda x: (np.abs(x - mean_frame)).mean(axis=None), frame_buffer)]
        avg_l1 = sum(l1) / len(l1)
        best_l1 = min(l1)

        # Select the frame that is the most similar to the mean
        best_frame = frame_buffer[0]
        for index, l1_score in enumerate(l1):
            if l1_score == best_l1:
                best_frame = frame_buffer[index]
                break
        best_frame = best_frame.astype(np.uint8)

        return avg_l1 <= self.__stability, best_frame

    def process(self) -> List[Tuple[imageio.core.Image, float]]:
        """
        Analyzes the video to detect the gestures present in it.
        :return: A list of tuples containing at position:
            0: gesture frame (as imageio.core.Image)
            1: timestamp (in seconds)
        """

        gestures = []
        reader = imageio.get_reader(self.__video_path)
        frame_buffer = []
        for index, frame in enumerate(reader):
            new_frame = self.__enhance_frame(frame)
            frame_buffer.append(new_frame)
            if len(frame_buffer) == self.__stable_frames:
                stable, gesture_frame = self.__check_stability(frame_buffer)
                if stable:
                    gestures.append((gesture_frame, self.__compute_seconds(index-self.__stable_frames+1)))
                frame_buffer = frame_buffer[self.__gesture_interval:]

        return gestures


if __name__ == '__main__':
    original_vid = "../../tmp/tmp_video.mp4"
    mediapipe_vid = "../../tmp/tmp_video_out.mp4"
    output_dir = "../../tmp/frame_test/"

    identifier = GestureIdentifier(mediapipe_vid, stable_frames=5, gesture_interval=3)
    stable_gestures = identifier.process()
    print("Stable gestures found: {n}".format(n=len(stable_gestures)))
    for g in stable_gestures:
        imageio.imwrite("{base}gesture_{n:.3f}.jpg".format(base=output_dir, n=g[1]), g[0])
