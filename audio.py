import sounddevice as sd
from scipy.io.wavfile import read
from dotenv import load_dotenv
from os import getenv

load_dotenv()

def play_wav_file(path):

    output_id = int(getenv('AUDIO_OUTPUT_ID'), base=10)

    sd.default.device[1] = output_id
    
    sampling_rate, data = read(path)

    sd.play(data=data, samplerate=sampling_rate, blocking=True)




