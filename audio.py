import sounddevice as sd
from scipy.io.wavfile import read
from dotenv import load_dotenv
from os import getenv
load_dotenv()

def play_wav_file(path):

    output_id = getenv('AUDIO_OUTPUT_ID')

    sd.default.device[1] = output_id
    
    sampling_rate, data = read(path)

    sd.play(data=data, samplerate=sampling_rate)

    sd.wait()



