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

CHUNK_SIZE = 1024
IN_RATE = 16000
OUT_RATE = 44100
CONFIG_PATH = Path(__file__).parent / Path('../config.json')
MODEL_PATH = Path(__file__).parent / Path('models/assets/vosk-model-small-en-us-0.15')
CHIME_PATH = Path(__file__).parent / Path('../sounds/chime.wav')

with open(CONFIG_PATH, 'r') as f:
    bb_config = json.load(f)

class Audio:

    def __init__(self) -> None:
        self._audio = None

    def __enter__(self):
        self._audio = pyaudio.PyAudio()
        return self._audio
    
    def __exit__(self, exc_type, exc_value, traceback):
        self._audio.terminate()
    

class Speaker:
    def __init__(self, audio):
        self._audio = audio
        self._stream = None

    def __enter__(self):
        self._stream = self._audio.open(format=pyaudio.paFloat32,
                                  channels=1,
                                  rate=OUT_RATE,  # Ensure this rate matches the sample rate of the TTS model
                                  output=True)
        return self._stream

    def __exit__(self, exc_type, exc_value, traceback):
        self._stream.stop_stream()
        self._stream.close()

class Microphone:
    def __init__(self, audio, rate=IN_RATE, chunk=CHUNK_SIZE, device_index=None):
        self._audio = audio
        self._stream = None
        self._rate = rate
        self._chunk=1024
        self._device_index = device_index

    def __enter__(self):
        self._stream = self._audio.open(format=pyaudio.paInt16,
                                        channels=1,
                                        rate=self._rate,
                                        input=True,
                                        frames_per_buffer=self._chunk,
                                        input_device_index=self._device_index)
        return self._stream

    def __exit__(self, exc_type, exc_value, traceback):
        self._stream.stop_stream()
        self._stream.close()

