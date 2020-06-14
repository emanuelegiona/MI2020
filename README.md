# MI2020
Project for Multimodal Interaction course (A.Y. 2019/2020)

## License
Code contained in this repository is distributed under [AGPL-3.0 license][license], exceptions below.

Authors<sup>1</sup>: [Angelo Di Mambro][auth1], [Emanuele Giona][auth2].

<small>1: equal contribution, alphabetic ordering is applied</small>
<hr>

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
