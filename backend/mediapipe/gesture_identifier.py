"""
This file contains all the necessary code to detect stable gestures in a Google MediaPipe-produced video.
"""

import os
import numpy as np
import imageio
from skimage.exposure import match_histograms
from skimage.metrics import structural_similarity

from typing import List, Tuple, Optional


class GestureIdentifier:

    def __init__(self, video_path: str,
                 stable_frames: int = 3,
                 apply_histogram_matching: bool = False,
                 use_structural_similarity: bool = False,
                 instability_threshold: float = 2.5,
                 gesture_frames_interval: int = 1,
                 gesture_time_interval: float = 2.0,
                 black_threshold: float = 0.995,
                 ln_norm: int = 3,
                 prev_gesture_threshold: float = 0.0003,
                 debug: bool = False):
        """
        Processes a MediaPipe-produced video to detect gestures in it.
        :param video_path: Path to the video to analyze
        :param stable_frames: Number of frames required to detect a gesture
        :param apply_histogram_matching: Whether to apply histogram matching to any two subsequent frames
        (default: False)
        :param use_structural_similarity: Whether to use structural similarity in gesture identification and duplicate
        avoidance (default: False)
        :param instability_threshold: Instability threshold (1 = exact same frame)
        :param gesture_frames_interval: Number of frames to skip between gestures
        :param gesture_time_interval: Time to skip between two subsequent gestures are recognized (in seconds)
        :param black_threshold: Black percentage threshold to discard stable frames with no gestures
        :param ln_norm: Ln norm to use when comparing two subsequent gesture frames (default: L3 norm)
        :param prev_gesture_threshold: Ceiling value for Ln norm value between two subsequent gesture frames
        :param debug: Whether to print debug information and save every landmark detected
        :raises FileNotFoundError, ValueError for invalid video file path
        """

        if not os.path.exists(video_path):
            raise FileNotFoundError("No video file found.")
        elif not os.path.isfile(video_path):
            raise ValueError("The provided path is not a regular file.")

        self.__video_path = video_path
        self.__stable_frames = stable_frames
        self.__histogram_matching = apply_histogram_matching
        self.__use_ssim = use_structural_similarity
        self.__instability_threshold = instability_threshold
        self.__gesture_frames_interval = gesture_frames_interval
        self.__gesture_time_interval = gesture_time_interval
        self.__black_threshold = black_threshold
        self.__ln_norm = ln_norm
        self.__prev_gesture_threshold = prev_gesture_threshold
        self.__debug = debug

        reader = imageio.get_reader(video_path)
        metadata = reader.get_meta_data()
        self.__total_frames = len([*enumerate(reader)])
        self.__fps = metadata["fps"]
        self.__duration = metadata["duration"]

    @staticmethod
    def __enhance_frame(frame: imageio.core.Image,
                        prev_frame: Optional[imageio.core.Image] = None,
                        histogram_matching: bool = False
                        ) -> (imageio.core.Image, imageio.core.Image):
        """
        Enhances the outline of landmarks in a frame, making all the rest black.
        :param frame: A frame from a MediaPipe-produced video
        :param prev_frame: The predecessor of the current frame (Optional)
        :param histogram_matching: Whether to apply histogram matching to the current frame w.r.t. to the previous one
        :return: The given frame with yellow landmarks and all the rest being black
        """

        # Stabilize image colors w.r.t. the previous frame (WARNING: performance hit)
        if histogram_matching and prev_frame is not None:
            frame = match_histograms(frame, prev_frame, multichannel=True)

        # Extract gesture only
        # TODO: this is the culprit
        array = np.copy(imageio.core.asarray(frame)) if histogram_matching else imageio.core.asarray(frame)
        mask_green = (np.any(array == (0, 255, 0), axis=-1))
        mask_red = (np.any(array == (255, 0, 0), axis=-1))
        array[np.logical_not(mask_green)] = [0, 0, 0]
        array[np.logical_not(mask_red)] = [0, 0, 0]
        array[(np.all(array == (255, 255, 255), axis=-1))] = [0, 0, 0]

        return imageio.core.Image(array), frame

    def __compute_seconds(self, index: int) -> float:
        """
        Given the frame number, computes the timestamp of occurrence in seconds.
        :param index: Number of frame
        :return: Timestamp of occurrence in seconds
        """
        return float(index)/self.__total_frames * self.__duration

    @staticmethod
    def __normalize(frames: List[imageio.core.Image]) -> List[np.ndarray]:
        """
        Applies normalization to the given images.
        :param frames: List of frames to normalize
        :return: List of normalized frames as List[np.ndarray]
        """

        frames = [*map(imageio.core.asarray, frames)]
        frames = [*map(lambda x: x.astype(np.float32), frames)]
        frames = [*map(lambda x: np.average(x, axis=-1), frames)]
        frames = [*map(lambda x: (x - x.min()) * 255 / (x.max() - x.min()), frames)]

        return frames

    def __ln_distance(self,
                      frames: List[imageio.core.Image],
                      normalize: bool = True,
                      ln_distance: int = 1
                      ) -> (List[np.ndarray], List[float], float):
        """
        Computes Ln distance in a group of frames w.r.t. to the mean frame, also computing the average Ln distance.
        :param frames: List of frames to compare
        :param normalize: Apply normalization (default: True)
        :param ln_distance: Ln distance to use (default: L1 distance)
        :return: Tuple containing at positions:
                    - 0: List of (normalized) frames
                    - 1: List of Ln distances from the mean frame
                    - 2: Average of Ln distances
        """

        # Compute the mean frame of the buffer
        if normalize:
            frames = GestureIdentifier.__normalize(frames)
        mean_frame = sum(frames) / len(frames)

        # Compute L1 or Ln distances and their average across all the frames
        def ln_dist_func(x: int) -> np.ndarray:
            return np.power(x, ln_distance) if ln_distance > 1 else x
        distances = [*map(lambda x: (ln_dist_func(np.abs(x - mean_frame))).mean(axis=None), frames)]
        avg_distance = sum(distances) / len(distances)

        if self.__debug:
            print(f"DEBUG\nDistances: {distances}\n Average distance: {avg_distance}")

        return frames, distances, avg_distance

    def __structural_similarity(self,
                                frames: List[imageio.core.Image],
                                normalize: bool = True
                                ) -> (List[np.ndarray], List[float], float):
        """
        Computes pairwise structural similarities in a group of frames, also computing the average structural similarity.
        :param frames: List of frames to compare
        :param normalize: Apply normalization (default: True)
        :return: Tuple containing at positions:
                    - 0: List of (normalized) frames
                    - 1: List of pairwise structural similarities
                    - 2: Average of structural similarities
        """

        if normalize:
            frames = GestureIdentifier.__normalize(frames)

        # Compute pairwise structural similarities and their average across all the frames
        frame_cache = []

        def pairwise_ssim(x):
            nonlocal frame_cache
            frame_cache.append(x)
            if len(frame_cache) == 2:
                ssim = structural_similarity(frame_cache[0], frame_cache[1])
                frame_cache = frame_cache[1:]
                return ssim
            else:
                return None

        ssims = [*map(pairwise_ssim, frames)]
        ssims = [*filter(lambda x: x is not None, ssims)]
        avg_ssim = sum(ssims) / len(ssims)

        if self.__debug:
            print(f"DEBUG\nSimilarities: {ssims}\n Average similarity: {avg_ssim}")

        return frames, ssims, avg_ssim

    def __check_stability(self, last_gesture: Optional[imageio.core.Image],
                          frame_buffer: List[imageio.core.Image],
                          use_structural_similarity: bool = False
                          ) -> (bool, Optional[imageio.core.Image]):
        """
        Computes stability of a list of frames, avoiding duplicate subsequent gestures.
        :param last_gesture: Frame associated with its immediate previous gesture
        :param frame_buffer: List of frames to evaluate
        :param use_structural_similarity: Whether to use structural similarity (default: False)
        :return: Tuple containing at positions:
                    - 0: Bool indicating whether the list of frames is stable
                    - 1: Best frame in case frames are stable, or None otherwise
                 Note: 'best frame':
                    - for Ln distances, it's the one closest to the mean frame
                    - for structural similarities, the one closest to its predecessor frame
        """

        # Discard unstable frames
        if use_structural_similarity:
            frame_buffer, metric_values, avg_metric_value = self.__structural_similarity(frame_buffer)
            if avg_metric_value <= self.__instability_threshold:
                return False, None
            # Select the frame that is the most similar to its predecessor
            best_metric_value = max(metric_values)
        else:
            frame_buffer, metric_values, avg_metric_value = self.__ln_distance(frame_buffer)
            if avg_metric_value > self.__instability_threshold:
                return False, None
            # Select the frame that is the most similar to the mean
            best_metric_value = min(metric_values)

        best_frame = frame_buffer[0]
        for index, metric_value in enumerate(metric_values):
            if metric_value == best_metric_value:
                best_frame = frame_buffer[index]
                break
        best_frame = best_frame.astype(np.uint8)

        # Discard frames with too much black (-> no gestures present)
        black_percent = np.sum(best_frame == 0, dtype=np.float32)
        black_percent = float(black_percent / best_frame.size)
        if black_percent > self.__black_threshold:
            return False, None
        # Discard gestures that are too similar to its immediate predecessor
        if last_gesture is not None:
            if use_structural_similarity:
                _, _, avg_ssim = self.__structural_similarity([last_gesture, best_frame],
                                                              normalize=False)
                if avg_ssim >= self.__prev_gesture_threshold:
                    return False, None
            else:
                mask = np.not_equal(last_gesture, 255)
                _, _, avg_ln = self.__ln_distance([last_gesture[mask], best_frame[mask]],
                                                  normalize=False,
                                                  ln_distance=self.__ln_norm)
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
        last_frame = None
        last_gesture = None
        for index, frame in enumerate(reader):
            landmarks, new_frame = self.__enhance_frame(frame, last_frame, histogram_matching=self.__histogram_matching)
            last_frame = new_frame
            if self.__debug:
                gestures.append((landmarks, self.__compute_seconds(index - self.__stable_frames + 1)))
            frame_buffer.append(landmarks)
            if len(frame_buffer) == self.__stable_frames:
                stable, gesture_frame = self.__check_stability(last_gesture,
                                                               frame_buffer,
                                                               use_structural_similarity=self.__use_ssim)
                if stable:
                    seconds = self.__compute_seconds(index - self.__stable_frames + 1)
                    # if the difference between new gesture and last gesture timestamps
                    # is >= gesture_time_interval, the new gesture is added.
                    if (last_gesture is not None and seconds - gestures[-1][1] >= self.__gesture_time_interval) or \
                            (last_gesture is None):
                        gestures.append((gesture_frame, seconds))
                        last_gesture = gesture_frame
                frame_buffer = frame_buffer[self.__gesture_frames_interval:]

        return gestures


if __name__ == '__main__':
    mediapipe_vid = "../../tmp/tmp_video_out.mp4"
    #mediapipe_vid = "../../tmp/tmp_video_out_angelo.mp4"
    output_dir = "../../tmp/frame_test/"
    #output_dir = "../../tmp/frame_test_angelo/"

    debug = False
    histogram_preprocess = False
    ssim = False
    if ssim:
        ssim_stability_threshold = 0.95
        ssim_too_similar_threshold = 0.95
        identifier = GestureIdentifier(mediapipe_vid,
                                       stable_frames=7,
                                       apply_histogram_matching=histogram_preprocess,
                                       use_structural_similarity=ssim,
                                       instability_threshold=ssim_stability_threshold,
                                       gesture_frames_interval=3,
                                       prev_gesture_threshold=ssim_too_similar_threshold,
                                       debug=debug)
    else:
        identifier = GestureIdentifier(mediapipe_vid,
                                       stable_frames=5,
                                       apply_histogram_matching=histogram_preprocess,
                                       gesture_frames_interval=3,
                                       debug=debug)
    stable_gestures = identifier.process()
    print("Stable gestures found: {n}".format(n=len(stable_gestures)))
    for g in stable_gestures:
        imageio.imwrite("{base}gesture_{n:.3f}.jpg".format(base=output_dir, n=g[1]), g[0])
