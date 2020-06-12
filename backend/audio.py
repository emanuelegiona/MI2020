"""
This file contains source code for all the audio processing involved in this project.
"""
import sounddevice as sd
import soundfile as sf
import os
import time
from pydub import AudioSegment

sd.default.samplerate = 16000


class Audio:

    def __init__(self, path: str = None, blocking: bool = False):
        """
        :param path: the path where the audio will be stored in.
        :param blocking: a flag that indicates if the recording will be blocking or not.
        """
        self.path = path
        self.start = None
        self.end = None
        self.audio = None
        self.block = blocking

    def rec(self, duration: float, fs: int = sd.default.samplerate):
        """
        Records and returns an audio sample from default device. If path is not None, the sample will be locally stored
        to path.
        :param duration: is an integer that indicates how many seconds of recording will be performed.
        :param fs: is the frequency sampling (sampling rate) of the captured audio expressed as an integer
        otherwise.
        """
        print("Start Recording")
        self.start = time.time()
        # recorded audio as a NumPy array
        self.audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, blocking=self.block)
        if self.path is not None and self.block is True:
            self.end = time.time()
            print("End Recording")
            sf.write(self.path, self.audio, fs)

    def read_from_file(self):
        """
        Read the audio file stored in the FS.
        :return: the audio data (as a Numpy array) and the related sample rate (as an integer).
        """
        data, fs = sf.read(self.path, dtype='float32')
        return data, fs

    @staticmethod
    def set_sample_rate(sm: int):
        """
        Set the sample rate for recording.
        :param sm: is the frequency sampling (sampling rate) of the captured audio expressed as an integer.
        """
        sd.default.samplerate = sm

    @staticmethod
    def get_sample_rate():
        """
        Return the sample rate for recording.
        :return the frequency sampling (sampling rate) of the captured audio expressed as an integer.
        """
        return sd.default.samplerate

    def stop(self):
        """
        Stops a non blocking rec() during an audio acquisition. The registration is immediately terminated without
        waiting for the timeout expressed by the duration argument of rec.
        """
        sd.stop()
        if self.path is not None:
            print("End Recording")
            self.end = time.time()
            sf.write(self.path, self.audio, self.get_sample_rate())
            duration = self.get_real_duration() * 1000
            audio = AudioSegment.from_wav(self.path)[:duration]
            self.delete()
            audio.export(self.path, format="wav")
            self.audio, fs = self.read_from_file()

    @staticmethod
    def wait():
        """
        If the recording was already finished, this returns immediately; if not, it waits and returns as soon as the
        recording is finished.
        :return: a flag indicating the status of recording.
        """
        return sd.wait()

    def delete(self):
        """
        Delete the recorded audio from FS.
        """
        if self.start is not None:
            os.remove(self.path)
        else:
            raise FileNotFoundError("{file} not found.".format(file=self.path))

    def get_real_duration(self):
        """
        In case of non-blocking audio this method returns the real duration of the audio, removing eventual final
        silences.
        :return: an integer indicating the real audio duration.
        """
        return self.end - self.start


if __name__ == "__main__":
    a = Audio("../tmp/audio.wav")
    a.rec(60)
    time.sleep(5)
    a.stop()
    data, fs = sf.read(a.path)
    sd.play(data, fs)
