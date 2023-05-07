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
import vosk
import time
from vosk import Model, KaldiRecognizer
from scipy import signal
import numpy as np
from barkbright import bb_config, IN_RATE

MODEL_RATE = 16000
MAX_INT16 = (2**15 - 1)
vosk.SetLogLevel(-1)

def listen(parent_conn):
    model = Model(model_path=bb_config['vosk_model_path'])
    recognizer = KaldiRecognizer(model, MODEL_RATE)
    recognizer.SetWords(True)
    recognizer.SetPartialWords(True)
    wake_word = False
    sleep_word = False
    start = None
    print("Running...")
    while True:
        audio = b''
        while parent_conn.poll():
            audio += parent_conn.recv_bytes()
        np_audio = np.frombuffer(audio, dtype=np.int16)
        np_audio_float = np_audio.astype(np.float32, order='C') / MAX_INT16
        np_audio_float = signal.resample_poly(np_audio_float, MODEL_RATE, IN_RATE)
        np_audio = (np_audio_float * MAX_INT16).astype(np.int16)
        audio = np_audio.tobytes()
        if recognizer.AcceptWaveform(audio):
            phrase = str(json.loads(recognizer.Result())['text'])
            wake_word = bb_config['wakeword'] in phrase or wake_word
            sleep_word = bb_config['sleep_word'] in phrase or sleep_word
            if phrase and wake_word:
                if sleep_word:
                    index = phrase.find(bb_config['sleep_word'])
                    if index != -1:
                        phrase = phrase[:index] + bb_config['sleep_word']
                    wake_word = False
                    sleep_word = False
                else:
                    index = phrase.find(bb_config['wakeword'])
                    if index != -1:
                        phrase = phrase[:index] + phrase[index+len(bb_config['wakeword']):]
                yield phrase
        else:
            partial_result = json.loads(recognizer.PartialResult())['partial'].lower()
            wake_word = bb_config['wakeword'] in partial_result or wake_word
            sleep_word = bb_config['sleep_word'] in partial_result or sleep_word
