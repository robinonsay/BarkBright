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
from pathlib import Path
from datetime import datetime
from barkbright.models.intent import IntentMatchingModel
from barkbright import Audio, Speaker, Microphone, CHUNK_SIZE, bb_config, IN_RATE
from barkbright import parsing, dialogue
from dataset import BB_INTENTS
from barkbright.models import asr
from barkbright.iot.neopixel import NeoPixelLEDStrip
from barkbright.colors import COLOR_MAP
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection

def main(train=False):
    dialogue.load_dialogue()
    global SAMP_WIDTH
    intent_model = IntentMatchingModel()
    if train:
        print('Training...')
        start = datetime.now()
        intent_model.train()
        delta = datetime.now() - start
        print(f" Training Time: {delta.total_seconds()}:.1f")
        intent_model.save()
    else:
        intent_model.load()
    phrases = list()
    num_new_phrases = 0
    data = list()
    intent = None
    parent_mic_conn, child_mic_conn = Pipe()
    prcs = Process(target=process_audio, args=(child_mic_conn,))
    prcs.start()
    parent_speaker_conn, child_speaker_conn = Pipe()
    prcs = Process(target=process_speak, args=(child_speaker_conn,))
    prcs.start()
    with NeoPixelLEDStrip(**bb_config['led_config']) as np_leds:
        try:
            for phrase, is_done in asr.listen(parent_mic_conn):
                if not (phrase == '' or phrase is None):
                    if phrase == 'wakeword':
                        parent_mic_conn.send({'run': True, 'record':False})
                        parent_speaker_conn.send({'intent': phrase, 'reset': is_done})
                        parent_speaker_conn.recv()
                        parent_mic_conn.send({'run': True, 'record':True})
                        np_leds[:] = COLOR_MAP['aqua']
                    elif phrase == 'sleep_word':
                        parent_speaker_conn.send({'intent': phrase, 'reset': is_done})
                        parent_speaker_conn.recv()
                        np_leds[:] = COLOR_MAP['black']
                    else:
                        sub_phrases = parsing.split_on_conj(phrase)
                        intent = intent_model.predict(sub_phrases)
                        for i, p in enumerate(sub_phrases):
                            intent_str = intent[i,0]
                            print(intent_str)
                            parent_mic_conn.send({'run': True, 'record':False})
                            parent_speaker_conn.send({'intent': intent_str, 'reset': is_done})
                            parent_speaker_conn.recv()
                            parent_mic_conn.send({'run': True, 'record':True})
                            if intent_str == 'on':
                                np_leds[:] = COLOR_MAP['white']
                            elif intent_str == 'off':
                                np_leds[:] = COLOR_MAP['black']
                            elif intent_str == 'color':
                                words = p.split()
                                for word in words:
                                    if word in COLOR_MAP:
                                        np_leds[:] = COLOR_MAP[word]
        finally:
            parent_mic_conn.send({'run': False, 'record':True})
            parent_speaker_conn.send(False)

def process_speak(conn):
    dialogue.load_dialogue()
    run = True
    device_index = None
    with Audio() as audio:
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
                run = False
        previous_intent = "none"
        while run:
            obj = conn.recv()
            if isinstance(obj, dict):
                intent = obj['intent']
                if intent in dialogue.dialogue and previous_intent in dialogue.dialogue[intent]:
                    size = len(dialogue.dialogue[intent][previous_intent]) - 1
                    filename = f"{intent}_{previous_intent}_{random.randint(0, size)}.wav"
                    file_path = Path(__file__).parent.parent / 'barkvoice' / 'sounds' / filename
                    chime_audio = None
                    with wave.open(file_path.as_posix(), 'rb') as chime:
                        chime_config = {'format':audio.get_format_from_width(chime.getsampwidth()),
                                        'channels':chime.getnchannels(),
                                        'rate':chime.getframerate(),
                                        'output':True,
                                        'output_device_index': device_index}
                        chime_audio = chime.readframes(chime.getnframes())
                    with Speaker(audio, **chime_config) as speaker:
                        speaker.write(chime_audio)
                if obj['reset']:
                    previous_intent = "none"
                else:
                    previous_intent = intent
            else:
                run = intent
            conn.send(True)
        
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
            record = True
            while run:
                if record:
                    audio = mic.read(CHUNK_SIZE, exception_on_overflow=False)
                    conn.send_bytes(audio)
                if conn.poll():
                    obj = conn.recv()
                    run = obj['run']
                    if record and not obj['record']:
                        mic.stop_stream()
                        record = False
                    elif not record and obj['record']:
                        mic.start_stream()
                        record = True
                    

