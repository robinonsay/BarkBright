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
import pyaudio
import json
from vosk import Model, KaldiRecognizer
from pathlib import Path
from barkbright import bb_config, MODEL_PATH, CHUNK_SIZE, RATE

def listen(mic:pyaudio.Stream, model_path=None, rate=RATE, chunk=CHUNK_SIZE, device_index=None) -> str:
    model = model_path if model_path else Model(model_path=MODEL_PATH.as_posix())
    recognizer = KaldiRecognizer(model, rate)
    recognizer.SetWords(True)
    recognizer.SetPartialWords(True)
    while True:
        data = mic.read(chunk, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())['text'].split()
            if result and bb_config['wakeword'] == result[0]:
                result.pop(0)
                phrase = ' '.join(result)
                print(phrase)
                yield phrase
