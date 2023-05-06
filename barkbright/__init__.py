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
import pyaudio
from pathlib import Path

CHUNK_SIZE = 4096
IN_RATE = 44100
OUT_RATE = 44100
CONFIG_PATH = Path(__file__).parent / Path('../config.json')
DEFAULT_PATH = Path(__file__).parent / Path('../default.json')

with open(DEFAULT_PATH, 'r') as f:
    bb_config = json.load(f)

with open(CONFIG_PATH, 'r') as f:
    user_config = json.load(f)
    for key in bb_config.keys():
        if key in user_config:
            bb_config[key] = user_config[key]

class Audio:

    def __init__(self) -> None:
        self._audio = None

    def __enter__(self):
        self._audio = pyaudio.PyAudio()
        return self._audio
    
    def __exit__(self, exc_type, exc_value, traceback):
        self._audio.terminate()
    

class Speaker:
    def __init__(self, audio, **kwargs):
        self._audio = audio
        self._stream = None
        self._kwargs = kwargs

    def __enter__(self):
        self._stream = self._audio.open(**self._kwargs)
        return self._stream

    def __exit__(self, exc_type, exc_value, traceback):
        self._stream.stop_stream()
        self._stream.close()

class Microphone:
    def __init__(self, audio, **kwargs):
        self._audio = audio
        self._stream = None
        self._kwargs = kwargs

    def __enter__(self):
        self._stream = self._audio.open(**self._kwargs)
        return self._stream

    def __exit__(self, exc_type, exc_value, traceback):
        self._stream.stop_stream()
        self._stream.close()

