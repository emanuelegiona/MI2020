"""
This file contains a Python wrapper to interact with a Google MediaPipe previously installed (see config.json file).
"""

import os
import json

# Global variables targeting the multi-hand tracking task in MediaPipe
MEDIAPIPE_SUBPATH = "mediapipe/examples/desktop/multi_hand_tracking"
TARGET = "multi_hand_tracking_cpu"
COMPILE_STR = "bazel build -c opt --define MEDIAPIPE_DISABLE_GPU=1 {path}:{target}"
EXEC_STR = "GLOG_logtostderr=1 {runnable} --calculator_graph_config_file={calculator}"


class MediaPipeHelper:

    def __init__(self, mediapipe_dir: str):
        """
        Helper class to run Google MediaPipe from Python.
        :param mediapipe_dir: Absolute directory pointing to the installation directory of MediaPipe
        """

        if not os.path.exists(mediapipe_dir):
            raise FileNotFoundError("Invalid MediaPipe installation directory.")
        elif not os.path.isabs(mediapipe_dir):
            raise ValueError("An absolute path must be provided.")
        elif not os.path.isdir(mediapipe_dir):
            raise NotADirectoryError("The provided path is not a directory.")

        contents = os.listdir(mediapipe_dir)
        if "WORKSPACE" not in contents:
            raise ValueError("MediaPipe installation directory must contain a WORKSPACE file.")

        self.__mediapipe_dir = mediapipe_dir
        self.__compile_str = COMPILE_STR.format(path=MEDIAPIPE_SUBPATH,
                                                target=TARGET)
        self.__exec_str = EXEC_STR.format(runnable=os.path.join(self.__mediapipe_dir,
                                                                "bazel-bin",
                                                                MEDIAPIPE_SUBPATH,
                                                                TARGET),
                                          calculator=os.path.join(self.__mediapipe_dir,
                                                                  "mediapipe",
                                                                  "graphs",
                                                                  "hand_tracking",
                                                                  "multi_hand_tracking_desktop_live.pbtxt"))

        # Moving to the MediaPipe's working dir
        curr_wd = os.getcwd()
        os.chdir(self.__mediapipe_dir)
        # Compiling MediaPipe's graph for multi-hand tracking
        os.system(self.__compile_str)
        # Restoring GesturePad's working dir
        os.chdir(curr_wd)

    def run(self, input_dir: str, output_dir: str) -> None:
        """
        Executes MediaPipe on the given input video exporting its results to the chosen path.
        :param input_dir: Path to the input video
        :param output_dir: Path to the output video to produce
        :return: None
        """

        command = "{exec} --input_video_path={input_dir} --output_video_path={output_dir}"
        command = command.format(exec=self.__exec_str,
                                 input_dir=input_dir,
                                 output_dir=output_dir)

        # Moving to the MediaPipe's working dir
        curr_wd = os.getcwd()
        os.chdir(self.__mediapipe_dir)
        # Compiling MediaPipe's graph for multi-hand tracking
        os.system(command)
        # Restoring GesturePad's working dir
        os.chdir(curr_wd)


if __name__ == '__main__':
    with open("../../data/config.json") as config_f:
        config = json.load(config_f)
    mediapipe_inst = config["mediapipe_dir"]
    print(mediapipe_inst)

    print("helper creation")
    helper = MediaPipeHelper(mediapipe_dir=mediapipe_inst)

    print("running on test.mp4")
    helper.run(input_dir="/home/emanuele/source/mi/MI2020/tmp/tmp_video.mp4",
               output_dir="/home/emanuele/source/mi/MI2020/tmp/tmp_video_out.mp4")
