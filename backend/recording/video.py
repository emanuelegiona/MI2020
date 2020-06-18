"""
This file contains source code for all the video processing involved in this project.
"""
import threading
import time
import os
import cv2
from backend.recording.audio import Audio
from typing import Tuple


class Video:

    def __init__(self, path: str, fps: float = 6, resolution: Tuple[int, int] = (640, 480)):
        """
        :param path: the path where the video will be stored in.
        :param fps: the frequency (rate) at which consecutive video frames are acquired.
        :param resolution: the resolution at which the video frames are acquired.
        """

        self.open = True
        self.device_index = 0
        self.fps = fps  # fps should be the minimum constant rate at which the camera can record
        self.fourcc = "MP4V"  # capture images (with no decrease in speed over time; testing is required)
        self.frameSize = resolution  # video formats and sizes also depend and vary according to the camera used
        self.video_filename = path
        self.video_cap = cv2.VideoCapture(self.device_index)
        self.video_writer = cv2.VideoWriter_fourcc(*self.fourcc)
        self.video_out = cv2.VideoWriter(self.video_filename, self.video_writer, self.fps, self.frameSize)
        self.frame_counts = 1
        self.start_time = time.time()

    def record(self) -> None:
        """
        Writes on file the video frame by frame showing to the user a recording window during the process.
        """

        while self.open:
            ret, video_frame = self.video_cap.read()
            if ret:
                self.video_out.write(video_frame)
                self.frame_counts += 1
                time.sleep(0.16)
                preview_color = cv2.cvtColor(video_frame, cv2.COLOR_RGB2RGBA)
                cv2.imshow('video_frame', preview_color)
                cv2.waitKey(1)
            else:
                break
                # 0.16 delay -> 6 fps

    def stop(self) -> None:
        """
        Stops the video recording.
        """

        if self.open:
            self.open = False
            self.video_out.release()
            self.video_cap.release()
            cv2.destroyAllWindows()

        else:
            pass

    def start(self) -> None:
        """
        Starts the video recording.
        """

        video_thread = threading.Thread(target=self.record)
        video_thread.start()


def file_manager(filename):
    localpath = os.getcwd()

    if os.path.exists(str(localpath) + "/audio.wav"):
        os.remove(str(localpath) + "/audio.wav")

    if os.path.exists(str(localpath) + "/" + filename + ".mp4"):
        os.remove(str(localpath) + "/" + filename + ".mp4")


if __name__ == "__main__":
    file_manager("tmp_video")
    v = Video("../../tmp/video.mp4")
    a = Audio("../../tmp/audio.wav")
    v.start()
    a.rec(60)
    time.sleep(10)
    v.stop()
    a.stop()
