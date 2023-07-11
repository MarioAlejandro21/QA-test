import winsound


def play_wav_file(path):
    winsound.PlaySound(path, winsound.SND_FILENAME)
