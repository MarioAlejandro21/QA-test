from sounddevice import play, wait
from soundfile import read
import winsound


def play_wav_file(path):
    winsound.PlaySound(path, winsound.SND_FILENAME)
