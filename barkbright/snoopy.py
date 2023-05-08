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
import random
import numpy as np
from scipy import signal
from pathlib import Path
from datetime import datetime
from barkbright.models.intent import IntentMatchingModel
from barkbright import Audio, Speaker, Microphone, CHUNK_SIZE, bb_config, IN_RATE
from barkbright import parsing
import barkbright.dialogue as dlg
from dataset import BB_INTENTS
from barkbright.models import asr
from barkbright.iot.neopixel import NeoPixelLEDStrip
from barkbright.colors import COLOR_MAP
from multiprocessing import Process, Pipe, Value
from multiprocessing.connection import Connection

def main():
    dlg.load_dialogue()
    intent_model = IntentMatchingModel()
    intent_model.load()
    intent = None
    running = Value('B', True)
    is_speaking = Value('B', False)
    parent_mic_conn, child_mic_conn = Pipe()
    prcs = Process(target=microphone, args=(child_mic_conn, is_speaking, running))
    prcs.start()
    parent_speaker_conn, child_speaker_conn = Pipe()
    prcs = Process(target=speaker, args=(child_speaker_conn, is_speaking, running))
    prcs.start()
    try:
        with NeoPixelLEDStrip(**bb_config['led_config']) as np_leds:
            transition = 'root'
            reset = True
            for phrase, is_done in asr.listen(parent_mic_conn):
                if phrase is None:
                    continue
                if len(phrase) == 0 and not is_done:
                    transition = 'root'
                    reset = False
                elif len(phrase) == 0 and is_done:
                    transition = 'sleep'
                    reset = True
                else:
                    sub_phrases = parsing.split_on_conj(phrase)
                    intent = intent_model.predict(sub_phrases)
                    for i, p in enumerate(sub_phrases):
                        intent_str = intent[i,0]
                        if reset and intent_str == 'unknown':
                            transition = 'root'
                            reset = False
                        else:
                            transition_map = dlg.dialogue[str(transition)]['transition']
                            if intent_str in transition_map:
                                transition = transition_map[intent_str]
                            else:
                                while 'hub' in transition_map:
                                    transition = transition_map['hub']
                                    transition_map = dlg.dialogue[str(transition)]['transition']
                                    if intent_str in transition_map:
                                        transition = transition_map[intent_str]
                                        break
                        if intent_str == 'on':
                            on(np_leds)
                        elif intent_str == 'off':
                            off(np_leds)
                        elif intent_str == 'color':
                            color_change(np_leds, p)
                        elif intent_str == 'increase':
                            increase_brightness(np_leds, p)
                        elif intent_str == 'decrease':
                            decrease_brightness(np_leds, p)
                is_speaking.value = True
                num_phrases = len(dlg.dialogue[str(transition)]['dialogue'].splitlines())
                parent_speaker_conn.send(f"{transition}_{random.randint(0, num_phrases - 1)}.wav")
                is_speaking.value = False
                if len(phrase) > 0 and is_done:
                    is_speaking.value = True
                    num_phrases = len(dlg.dialogue["sleep"]['dialogue'].splitlines())
                    parent_speaker_conn.send(f"sleep_{random.randint(0, num_phrases - 1)}.wav")
                    is_speaking.value = False

    finally:
        running.value = False

def on(np_leds:NeoPixelLEDStrip):
    np_leds[:] = COLOR_MAP['white']
    np_leds.show()

def off(np_leds:NeoPixelLEDStrip):
    np_leds[:] = COLOR_MAP['black']
    np_leds.show()

def color_change(np_leds:NeoPixelLEDStrip, phrase):
    for word in phrase.split():
        if word in COLOR_MAP:
            np_leds[:] = COLOR_MAP[word]
    np_leds.show()

def increase_brightness(np_leds:NeoPixelLEDStrip, phrase):
    for i, led in enumerate(np_leds):
        val = tuple([min(255, v+20) for v in led])
        np_leds[i] = val
    np_leds.show()

def decrease_brightness(np_leds:NeoPixelLEDStrip, phrase):
    for i, led in enumerate(np_leds):
        val = tuple([max(0, v-20) for v in led])
        np_leds[i] = val
    np_leds.show()


def get_audio_device(audio: pyaudio.PyAudio):
    device_index = None
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
            device_index = None
    return device_index

def speaker(conn:Connection, is_speaking:Value, run:Value):
    device_index = None
    with Audio() as audio:
        device_index = get_audio_device(audio)
        while run.value:
            filename = conn.recv()
            if isinstance(filename, str):
                is_speaking.value = True
                file_path = Path(__file__).parent.parent / 'barkvoice' / 'sounds' / filename
                audio_data = None
                with wave.open(file_path.as_posix(), 'rb') as voice:
                    chime_config = {'format':audio.get_format_from_width(voice.getsampwidth()),
                                    'channels':voice.getnchannels(),
                                    'rate':voice.getframerate(),
                                    'output':True,
                                    'output_device_index': device_index}
                    audio_data = voice.readframes(voice.getnframes())
                with Speaker(audio, **chime_config) as speaker:
                    speaker.write(audio_data)
                is_speaking.value = False

def microphone(conn:Connection, is_speaking:Value, run:Value):
    with Audio() as audio:
        device_index = get_audio_device(audio)
        config = {
            'format': pyaudio.paInt16,
            'channels': 1,
            'rate': IN_RATE,
            'input': True,
            'frames_per_buffer': CHUNK_SIZE,
            'input_device_index': device_index
        }
        with Microphone(audio, **config) as mic:
            print('Snooopy Listening...')
            record = True
            while run.value:
                if record and not is_speaking.value:
                    audio = mic.read(CHUNK_SIZE, exception_on_overflow=False)
                    conn.send_bytes(audio)
                elif record:
                    mic.stop_stream()
                    record = False
                elif not is_speaking.value:
                    mic.start_stream()
                    record = True

