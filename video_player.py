from os import startfile, getcwd
from os.path import join

def play_video(path):
    startfile(join(getcwd(), path))