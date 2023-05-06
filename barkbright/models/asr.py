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
from barkbright import Audio, Microphone, bb_config, CHUNK_SIZE, IN_RATE
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection

MODEL_RATE = 16000
MAX_INT16 = (2**15 - 1)

def listen(model_path=None) -> str:
    model = model_path if model_path else Model(model_path=bb_config['vosk_model_path'])
    recognizer = KaldiRecognizer(model, MODEL_RATE)
    recognizer.SetWords(True)
    recognizer.SetPartialWords(True)
    parent_conn, child_conn = Pipe()
    prcs = Process(target=process_audio, args=(child_conn,))
    prcs.start()
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
            if recognizer.AcceptWaveform(audio):
                result = json.loads(recognizer.Result())['text'].split()
                print(result)
                if result and bb_config['wakeword'] == result[0]:
                    print('AWAKE')
                    result.pop(0)
                    phrase = ' '.join(result)
                    yield phrase
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
