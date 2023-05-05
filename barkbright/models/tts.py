import pyaudio
import numpy as np
from TTS.api import TTS

TTS_MODEL = TTS(model_name='tts_models/en/ljspeech/tacotron2-DCA')

def tts(speaker:pyaudio.Stream, phrase):
    wav = np.array(TTS_MODEL.tts(phrase))
    speaker.write(wav.astype(np.float32).tobytes())
