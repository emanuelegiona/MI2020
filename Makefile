all: libs pip

libs:
	@echo "\nInstalling required packets using APT\n"
	sudo apt install libportaudio2

pip:
	@echo "\nInstalling Python packages using PIP\n"
	pip install soundfile
	pip install sounddevice
	pip install pydub
	pip install requests
	pip install appjar
