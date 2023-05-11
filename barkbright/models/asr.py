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
import json
import vosk
from vosk import Model, KaldiRecognizer
from scipy import signal
import numpy as np
from barkbright import bb_config, IN_RATE

MODEL_RATE = 16000
MAX_INT16 = (2**15 - 1)
vosk.SetLogLevel(-1)

def collect_data(parent_conn, ready) -> str:
    model = Model(model_path=bb_config['vosk_model_path'])
    recognizer = KaldiRecognizer(model, MODEL_RATE)
    recognizer.SetWords(True)
    recognizer.SetPartialWords(True)
    print('Running...')
    while True:
        audio = b''
        if not ready.value:
            ready.value = True
        audio = parent_conn.recv_bytes()
        np_audio = np.frombuffer(audio, dtype=np.int16)
        np_audio_float = np_audio.astype(np.float32, order='C') / MAX_INT16
        np_audio_float = signal.resample_poly(np_audio_float, MODEL_RATE, IN_RATE)
        np_audio = (np_audio_float * MAX_INT16).astype(np.int16)
        audio = np_audio.tobytes()
        if recognizer.AcceptWaveform(audio):
            phrase = str(json.loads(recognizer.Result())['text'])
            yield phrase

def listen(parent_conn, ready):
    model = Model(model_path=bb_config['vosk_model_path'])
    recognizer = KaldiRecognizer(model, MODEL_RATE)
    recognizer.SetWords(True)
    recognizer.SetPartialWords(True)
    is_wake_word = False
    is_sleep_word = False
    while True:
        audio = b''
        if not ready.value:
            ready.value = True
        while parent_conn.poll():
            audio += parent_conn.recv_bytes()
        np_audio = np.frombuffer(audio, dtype=np.int16)
        np_audio_float = np_audio.astype(np.float32, order='C') / MAX_INT16
        np_audio_float = signal.resample_poly(np_audio_float, MODEL_RATE, IN_RATE)
        np_audio = (np_audio_float * MAX_INT16).astype(np.int16)
        audio = np_audio.tobytes()
        if recognizer.AcceptWaveform(audio):
            phrase = str(json.loads(recognizer.Result())['text'])
            wakeword = is_wakeword(phrase)
            sleepword = is_sleepword(phrase)
            is_wake_word = wakeword or is_wake_word
            is_sleep_word = sleepword or is_sleep_word
            if phrase and is_wake_word:
                if wakeword:
                    index = phrase.find(wakeword)
                    if index != -1:
                        phrase = phrase[:index] + phrase[index+len(bb_config['wakeword']):]
                if is_sleep_word:
                    if sleepword:
                        index = phrase.find(sleepword)
                        if index != -1:
                            phrase = phrase[:index]
                    is_wake_word = False
                    yield phrase, is_sleep_word
                    is_sleep_word = False
                else:
                    yield phrase, is_sleep_word
        # else:
        #     partial_result = json.loads(recognizer.PartialResult())['partial'].lower()
        #     wakeword = is_wakeword(partial_result)
        #     sleepword = is_sleepword(partial_result)
        #     is_wake_word = wakeword or is_wake_word
        #     is_sleep_word = sleepword or is_sleep_word

def is_wakeword(phrase:str):
    ww = None
    for wakeword in bb_config['wakeword']:
        if wakeword in phrase:
            ww = wakeword
            break
    return ww

def is_sleepword(phrase:str):
    sw = None
    for sleepword in bb_config['sleep_word']:
        if sleepword in phrase:
            sw = sleepword
            break
    return sw
