"""
This file contains source code for all the video processing involved in this project.
"""

import time
import os
import cv2
import tkinter as tk
from PIL import Image, ImageTk
from backend.recording.audio import Audio
from typing import Tuple, Optional, Any


class Video:

    def __init__(self,
                 path: str,
                 fps: float = 6,
                 resolution: Tuple[int, int] = (640, 480),
                 root_window: Optional[Any] = None):
        """
        :param path: the path where the video will be stored in.
        :param fps: the frequency (rate) at which consecutive video frames are acquired.
        :param resolution: the resolution at which the video frames are acquired.
        :param root_window: Tkinter root window (if any)
        """

        self.device_index = 0
        self.fps = fps  # fps should be the minimum constant rate at which the camera can record
        self.fourcc = "MP4V"  # capture images (with no decrease in speed over time; testing is required)
        self.frameSize = resolution  # video formats and sizes also depend and vary according to the camera used
        self.video_filename = path
        self.video_cap = None
        self.video_writer = cv2.VideoWriter_fourcc(*self.fourcc)
        self.video_out = None
        self.frame_counts = 1
        self.start_time = time.time()

        self.__root_window = root_window
        self.tk_window = None
        self.tk_frame = None
        self.tk_label = None

    def record(self) -> None:
        """
        Writes on file the video frame by frame showing to the user a recording window during the process.
        """

        ret, video_frame = self.video_cap.read()
        if ret:
            self.video_out.write(video_frame)
            self.frame_counts += 1
            time.sleep(0.16)
            preview_color = cv2.cvtColor(video_frame, cv2.COLOR_BGR2RGB)

            img = Image.fromarray(preview_color)
            imgtk = ImageTk.PhotoImage(image=img)
            self.tk_label.imgtk = imgtk
            self.tk_label.configure(image=imgtk)

            self.tk_label.after(10, self.record)

            cv2.waitKey(1)

    def stop(self) -> None:
        """
        Stops the video recording.
        """

        if self.__root_window is None:
            self.tk_window.quit()
        else:
            self.tk_window.destroy()

        self.video_out.release()
        self.video_cap.release()
        cv2.destroyAllWindows()

    def start(self) -> None:
        """
        Starts the video recording.
        """

        self.tk_window = tk.Tk() if self.__root_window is None else tk.Toplevel(self.__root_window)
        self.tk_window.wm_title(
            "WebCam: {command} to stop recording".format(
                command="close window" if self.__root_window is None else "press Stop"
            )
        )
        self.tk_window.config(background="#FFFFFF")
        self.tk_frame = tk.Frame(self.tk_window, width=300, height=200)
        self.tk_frame.grid(row=0, column=0, padx=10, pady=2)
        self.tk_label = tk.Label(self.tk_frame)
        self.tk_label.grid(row=0, column=0)

        self.video_cap = cv2.VideoCapture(self.device_index)
        self.video_out = cv2.VideoWriter(self.video_filename, self.video_writer, self.fps, self.frameSize)
        self.frame_counts = 1
        self.start_time = time.time()

        self.record()
        if self.__root_window is None:
            self.tk_window.mainloop()


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

    a.rec(60)
    v.start()

    v.stop()
    a.stop()

    time.sleep(2)
    print("new video")
    v = Video("../../tmp/video.mp4")
    v.start()
    v.stop()
