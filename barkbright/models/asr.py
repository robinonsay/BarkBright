'''
Copyright 2023 Robin Onsay

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import wave
import pyaudio
import json
from vosk import Model, KaldiRecognizer
from pathlib import Path
from scipy import signal
import numpy as np
from barkbright import bb_config, MODEL_PATH, CHUNK_SIZE, IN_RATE

MODEL_RATE = 16000
MAX_INT16 = (2**15 - 1)

def listen(mic:pyaudio.Stream, model_path=None) -> str:
    model = model_path if model_path else Model(model_path=MODEL_PATH.as_posix())
    recognizer = KaldiRecognizer(model, IN_RATE)
    recognizer.SetWords(True)
    recognizer.SetPartialWords(True)
    with wave.open('test.wav', 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(MODEL_RATE)
        while True:
            audio = mic.read(CHUNK_SIZE, exception_on_overflow=False)
            np_audio = np.frombuffer(audio, dtype=np.int16)
            np_audio_float = np_audio.astype(np.float32, order='C') / MAX_INT16
            np_audio_float = signal.decimate(np_audio_float, IN_RATE // MODEL_RATE)
            np_audio = (np_audio_float * MAX_INT16).astype(np.int16)
            audio = np_audio.tobytes()
            f.writeframes(audio)
            if recognizer.AcceptWaveform(audio):
                result = json.loads(recognizer.Result())['text'].split()
                print(result)
                if result and bb_config['wakeword'] == result[0]:
                    result.pop(0)
                    phrase = ' '.join(result)
                    print(phrase)
                    yield phrase
