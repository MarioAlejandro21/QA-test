from pydub import AudioSegment
from pydub.playback import play


def play_mp3_file(path):
    
    sound = AudioSegment.from_mp3(path)
    play(sound)