# MI2020
Project for Multimodal Interaction course (A.Y. 2019/2020), codename GesturePad.

GesturePad is a text editor capable of producing HTML/Markdown documents allowing multiple input
modalities: *text* or *voice and gestures*.

The vocal interaction is based on a continuous, dictation-style, speaker-independent speech
recognition model implemented by [Google Cloud Speech-to-Text][speech].

The gesture interaction is based on [arbitrary semaphoric gestures][dataset], and their recognition
relies on hand landmarks detection by [Google MediaPipe][mediapipe], and the processed by a
cloud-deployed [Google Cloud Vision AutoML][automl] model.

Complete details can be found in the [PDF report][report].

#### [DEMO VIDEO](https://www.youtube.com/watch?v=vxee5DqA4Jo)

## Instructions
GesturePad has been developed on Ubuntu 18.04 (LTS) with Python 3.6+.
See further installation requirements for [Google MediaPipe][mediapipe].

In order to run this project, a [Makefile](./Makefile) has been set up to contain all
the required libraries and Python packages; for this reason the suggested
routine for running this project is the following:

1. Download (and unzip) or clone the project;

2. Move into the main directory (containing the Makefile);

3. Run the `make` command which will:
(a) install required system libraries,
(b) install the required Python packages,
(c) clone Google MediaPipe from its official GitHub repository, and
(d) patch the MediaPipe installation with our custom files;

4. Modify the `config.json` file according to your Google Cloud Platform subscription
and AutoML settings;

5. Run `gesture_pad.py` in the main project directory and follow the instructions in the GUI.

##### Note
It is advised to set up a Python virtual environment and to download/clone the project into a directory whose parent is not a root-protected directory.


## License
Code contained in this repository is distributed under [AGPL-3.0 license][license], exceptions below.
The file `dataset.zip` representing the gesture dataset created by us is distributed under
[CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

Authors<sup>1</sup>: [Angelo Di Mambro][auth1], [Emanuele Giona][auth2].

1: equal contribution, alphabetic ordering is applied

##### Acknowledgments

Files [demo_run_graph_main.cc][demo_graph], [end_loop_calculator.h][calculator1], and
[landmarks_to_render_data_calculator.cc][calculator2] are unmodified copies of the ones
present in the repository [Sign language recognition with RNN and Mediapipe][rabBit64repo],
which is property of [Anna Kim][rabBit64] and the same license of the original repository applies.

Files [multi_hand_renderer_cpu.pbtxt][renderer] and [multi_hand_tracking_desktop_live.pbtxt][tracking]
are original modifications of the ones present in the repository
[MediaPipe: Cross-platform ML solutions made simple][mediapiperepo], which is property of
Google's [MediaPipe team][mediapipe] and they are redistributed under the [same
AGPL-3.0 license][license] as the rest of this repository.

[license]: ./LICENSE
[auth1]: https://github.com/angelodimambro
[auth2]: https://github.com/emanuelegiona
[demo_graph]: ./data/mediapipe_custom/demo_run_graph_main.cc
[calculator1]: ./data/mediapipe_custom/end_loop_calculator.h
[calculator2]: ./data/mediapipe_custom/landmarks_to_render_data_calculator.cc
[rabBit64]: https://github.com/rabBit64
[rabBit64repo]: https://github.com/rabBit64/Sign-language-recognition-with-RNN-and-Mediapipe
[renderer]: ./data/mediapipe_custom/multi_hand_renderer_cpu.pbtxt
[tracking]: ./data/mediapipe_custom/multi_hand_tracking_desktop_live.pbtxt
[mediapiperepo]: https://github.com/google/mediapipe
[mediapipe]: https://mediapipe.dev/
[speech]: https://cloud.google.com/speech-to-text
[automl]: https://cloud.google.com/automl
[report]: ./anonymous_report.pdf
[dataset]: ./dataset.zip
