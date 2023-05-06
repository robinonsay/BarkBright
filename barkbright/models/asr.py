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
from pathlib import Path
from scipy import signal
import numpy as np
from barkbright import Audio, Microphone, bb_config, CHUNK_SIZE, IN_RATE
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection

MODEL_RATE = 16000
MAX_INT16 = (2**15 - 1)
vosk.SetLogLevel(-1)

def listen(model_path=None) -> str:
    model = model_path if model_path else Model(model_path=bb_config['vosk_model_path'])
    recognizer = KaldiRecognizer(model, MODEL_RATE)
    recognizer.SetWords(True)
    recognizer.SetPartialWords(True)
    parent_conn, child_conn = Pipe()
    prcs = Process(target=process_audio, args=(child_conn,))
    prcs.start()
    wake_word = False
    sleep_word = False
    start = None
    print("Running...")
    try:
        while True:
            audio = b''
            while parent_conn.poll():
                audio += parent_conn.recv_bytes()
            np_audio = np.frombuffer(audio, dtype=np.int16)
            np_audio_float = np_audio.astype(np.float32, order='C') / MAX_INT16
            np_audio_float = signal.resample_poly(np_audio_float, MODEL_RATE, IN_RATE)
            np_audio = (np_audio_float * MAX_INT16).astype(np.int16)
            audio = np_audio.tobytes()
            if wake_word:
                start = time.time_ns()
            if recognizer.AcceptWaveform(audio):
                phrase = str(json.loads(recognizer.Result())['text'])
                wake_word = bb_config['wakeword'] in phrase or wake_word
                sleep_word = bb_config['sleep_word'] in phrase or sleep_word
                if phrase and wake_word:
                    if sleep_word:
                        index = phrase.find(bb_config['sleep_word'])
                        phrase = phrase[:index]
                        print(phrase)
                        yield phrase
                        wake_word = False
                    else:
                        index = phrase.find(bb_config['wakeword'])
                        phrase = phrase[:index] + phrase[index+len(bb_config['wakeword']):]
                        phrase = 'wakeword' if phrase == '' else phrase
                        print(phrase)
                        yield phrase
            else:
                partial_result = json.loads(recognizer.PartialResult())['partial'].lower()
                wake_word = bb_config['wakeword'] in partial_result or wake_word
                sleep_word = bb_config['sleep_word'] in partial_result or sleep_word


    finally:
        parent_conn.send(False)

def process_audio(conn: Connection):
    run = True
    device_index = None
    with Audio() as audio:
        if bb_config['device'] == 'rpi':
            device_name = "USB Audio Device"
            device_index = -1
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                if device_name in device_info["name"]:
                    device_index = i
                    break

            if device_index == -1:
                print(f"Device '{device_name}' not found")
                run = False
        config = {
            'format': pyaudio.paInt16,
            'channels': 1,
            'rate': IN_RATE,
            'input': True,
            'frames_per_buffer': CHUNK_SIZE,
            'input_device_index': device_index
        }
        with Microphone(audio, **config) as mic:
            while run:
                audio = mic.read(CHUNK_SIZE, exception_on_overflow=False)
                conn.send_bytes(audio)
                if conn.poll():
                    run = conn.recv()
