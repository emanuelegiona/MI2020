all: libs pip mediapipe patch

libs:
	@echo "\nInstalling required packets using APT\n"
	sudo apt install libportaudio2

pip:
	@echo "\nInstalling Python packages using PIP\n"
	pip install numpy
	pip install opencv-python
	pip install tensorflow
	pip install shapely
	pip install scipy
	pip install pillow
	pip install imageio
	pip install imageio-ffmpeg
	pip install matplotlib
	pip install soundfile
	pip install sounddevice
	pip install pydub
	pip install requests
	pip install appjar

mediapipe:
	@echo "\nInstalling dependencies for Google MediaPipe\n"
	curl https://bazel.build/bazel-release.pub.gpg | sudo apt-key add -
	@echo "\nPress ENTER to continue...\n"
	echo "deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
	sudo apt update && sudo apt install bazel
	sudo apt install libopencv-core-dev libopencv-highgui-dev
	sudo apt install libopencv-calib3d-dev libopencv-features2d-dev
	sudo apt install libopencv-imgproc-dev libopencv-video-dev
	@echo "\nCloning Google MediaPipe from its GitHub repository\n"
	cd .. && \
	git clone https://github.com/google/mediapipe.git && \
	python MI2020/config_updater.py `pwd`

patch:
	@echo "\nReplacing original Google MediaPipe files with custom ones (also includes from github.com/rabBit64)\n"
	cd .. && \
	rm mediapipe/mediapipe/calculators/core/end_loop_calculator.h && \
	cp MI2020/data/mediapipe_custom/end_loop_calculator.h mediapipe/mediapipe/calculators/core/ && \
	rm mediapipe/mediapipe/calculators/util/landmarks_to_render_data_calculator.cc && \
	cp MI2020/data/mediapipe_custom/landmarks_to_render_data_calculator.cc mediapipe/mediapipe/calculators/util/ && \
	rm mediapipe/mediapipe/examples/desktop/demo_run_graph_main.cc && \
	cp MI2020/data/mediapipe_custom/demo_run_graph_main.cc mediapipe/mediapipe/examples/desktop/ && \
	rm mediapipe/mediapipe/graphs/hand_tracking/multi_hand_tracking_desktop_live.pbtxt && \
	cp MI2020/data/mediapipe_custom/multi_hand_tracking_desktop_live.pbtxt mediapipe/mediapipe/graphs/hand_tracking/ && \
	rm mediapipe/mediapipe/graphs/hand_tracking/subgraphs/multi_hand_renderer_cpu.pbtxt && \
	cp MI2020/data/mediapipe_custom/multi_hand_renderer_cpu.pbtxt mediapipe/mediapipe/graphs/hand_tracking/subgraphs/
