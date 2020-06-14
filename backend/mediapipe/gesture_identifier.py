"""
This file contains all the necessary code to detect stable gestures in a Google MediaPipe-produced video.
"""

import os
import numpy as np
import imageio

from typing import List, Tuple, Optional


class GestureIdentifier:

    def __init__(self, video_path: str,
                 stable_frames: int = 3,
                 instability_threshold: float = 2.5,
                 gesture_interval: int = 1,
                 white_threshold: float = 0.995,
                 ln_norm: int = 3,
                 prev_gesture_threshold: float = 1.8):
        """
        Processes a MediaPipe-produced video to detect gestures in it.
        :param video_path: Path to the video to analyze
        :param stable_frames: Number of frames required to detect a gesture
        :param instability_threshold: Instability threshold (1 = exact same frame)
        :param gesture_interval: Number of frames to skip between gestures
        :param white_threshold: White percentage threshold to discard stable frames with no gestures
        :param ln_norm: Ln norm to use when comparing two subsequent gesture frames (default: L3 norm)
        :param prev_gesture_threshold: Ceiling value for Ln norm value between two subsequent gesture frames
        :raises FileNotFoundError, ValueError for invalid video file path
        """

        if not os.path.exists(video_path):
            raise FileNotFoundError("No video file found.")
        elif not os.path.isfile(video_path):
            raise ValueError("The provided path is not a regular file.")

        self.__video_path = video_path
        self.__stable_frames = stable_frames
        self.__instability_threshold = instability_threshold
        self.__gesture_interval = gesture_interval
        self.__white_threshold = white_threshold
        self.__ln_norm = ln_norm
        self.__prev_gesture_threshold = prev_gesture_threshold

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

    @staticmethod
    def __frame_similarity(frames: List[imageio.core.Image],
                           normalize: bool = True,
                           ln_norm: int = 1
                           ) -> (List[np.ndarray], List[float], float):
        """
        Computes similarity among a group of frames in terms of Ln norms, also computing their averages.
        :param frames: List of frames to compare
        :param normalize: Apply normalization (default: True)
        :param ln_norm: Ln norm to use (default: L1 norm)
        :return: Tuple containing at positions:
                    - 0: List of normalized frames
                    - 1: List of Ln distances from the mean frame
                    - 2: Average of Ln distances
        """

        # Compute the mean frame of the buffer
        if normalize:
            frames = [*map(imageio.core.asarray, frames)]
            frames = [*map(lambda x: x.astype(np.float32), frames)]
            frames = [*map(lambda x: np.average(x, axis=-1), frames)]
            frames = [*map(lambda x: (x - x.min()) * 255 / (x.max() - x.min()), frames)]
        mean_frame = sum(frames) / len(frames)

        # Compute L1 or Ln norms and their average across all the frames
        def norm_func(x: int) -> np.ndarray:
            return np.power(x, ln_norm) if ln_norm > 1 else x
        norms = [*map(lambda x: (norm_func(np.abs(x - mean_frame))).mean(axis=None), frames)]
        avg_norm = sum(norms) / len(norms)

        return frames, norms, avg_norm

    def __check_stability(self, last_gesture: Optional[imageio.core.Image],
                          frame_buffer: List[imageio.core.Image]
                          ) -> (bool, Optional[imageio.core.Image]):
        """
        Computes stability of a list of frames, avoiding duplicate subsequent gestures.
        :param last_gesture: Frame associated with its immediate previous gesture
        :param frame_buffer: List of frames to evaluate
        :return: Tuple containing at positions:
                    - 0: Bool indicating whether the list of frames is stable
                    - 1: Best frame (most similar to the mean frame) in case frames are stable, or None otherwise
        """

        # Discard unstable frames
        frame_buffer, l1, avg_l1 = GestureIdentifier.__frame_similarity(frame_buffer)
        if avg_l1 > self.__instability_threshold:
            return False, None

        # Select the frame that is the most similar to the mean
        best_l1 = min(l1)
        best_frame = frame_buffer[0]
        for index, l1_score in enumerate(l1):
            if l1_score == best_l1:
                best_frame = frame_buffer[index]
                break
        best_frame = best_frame.astype(np.uint8)

        # Discard frames with too much white (-> no gestures present)
        white_percent = np.sum(best_frame == 255, dtype=np.float32)
        white_percent = float(white_percent / best_frame.size)
        if white_percent > self.__white_threshold:
            return False, None

        # Discard gestures that are too similar to its immediate predecessor
        if last_gesture is not None:
            mask = np.not_equal(last_gesture, 255)
            _, _, avg_ln = GestureIdentifier.__frame_similarity([last_gesture[mask], best_frame[mask]],
                                                                normalize=False,
                                                                ln_norm=self.__ln_norm)
            avg_ln /= 100**self.__ln_norm
            if avg_ln <= self.__prev_gesture_threshold:
                return False, None

        return True, best_frame

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
        last_gesture = None
        for index, frame in enumerate(reader):
            new_frame = self.__enhance_frame(frame)
            frame_buffer.append(new_frame)
            if len(frame_buffer) == self.__stable_frames:
                stable, gesture_frame = self.__check_stability(last_gesture, frame_buffer)
                if stable:
                    gestures.append((gesture_frame, self.__compute_seconds(index-self.__stable_frames+1)))
                    last_gesture = gesture_frame
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
