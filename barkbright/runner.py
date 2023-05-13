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
import re
import time
import numpy as np
from scipy import signal
from pathlib import Path
from datetime import datetime
from barkbright.models.intent import IntentMatchingModel
from barkbright import Audio, Speaker, Microphone, CHUNK_SIZE, bb_config, IN_RATE
from barkbright import parsing
from barkbright.word2num import word2num
from barkbright import dialogue as dlg
from barkbright.models import asr
from barkbright.iot.neopixel import NeoPixelLEDStrip, light_manager
from multiprocessing import Process, Pipe, Value
from multiprocessing.connection import Connection

def led_listening(light_mngr_conn, leds):
    third_len = len(leds) // 3
    leds[:third_len] = bb_config['colors']['bingo dark green']
    leds[third_len:-third_len] = bb_config['colors']['bingo dark green']
    leds[-third_len:] = bb_config['colors']['bingo dark green']
    light_mngr_conn.send(leds)

def main():
    dlg.load_dialogue()
    intent_model = IntentMatchingModel()
    intent_model.load()
    intent = None
    running = Value('B', True)
    run_function = Value('B', True)
    ready = Value('B', False)
    is_speaking = Value('B', False)
    parent_mic_conn, child_mic_conn = Pipe()
    prcs_mic = Process(target=microphone, args=(child_mic_conn, is_speaking, running, ready))
    parent_speaker_conn, child_speaker_conn = Pipe()
    prcs_spkr = Process(target=speaker, args=(child_speaker_conn, is_speaking, running))
    light_mngr_conn,  child_light_mngr_conn = Pipe()
    prcs_light_mngr = Process(target=light_manager, args=(child_light_mngr_conn, running, run_function))
    leds = np.zeros((bb_config['led_config']['count'], 3))
    try:
        prcs_light_mngr.start()
        led_listening(light_mngr_conn, leds)
        time.sleep(0.5)
        leds[:] = bb_config['colors']['black']
        light_mngr_conn.send(leds)
        prcs_mic.start()
        prcs_spkr.start()
        transition = 'root'
        reset = True
        for phrase, is_done in asr.listen(parent_mic_conn, ready):
            phrase = word2num(phrase)
            if phrase is None:
                continue
            if len(phrase) == 0 and not is_done:
                transition = 'root'
                led_listening(light_mngr_conn, leds)
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
                        run_function.value = False
                        on(light_mngr_conn, leds)
                    elif intent_str == 'off':
                        run_function.value = False
                        off(light_mngr_conn, leds)
                    elif intent_str == 'color':
                        run_function.value = False
                        color_change(light_mngr_conn, leds, p)
                    elif intent_str == 'increase':
                        run_function.value = False
                        increase_brightness(light_mngr_conn, leds, p)
                    elif intent_str == 'decrease':
                        run_function.value = False
                        decrease_brightness(light_mngr_conn, leds, p)
                    elif intent_str == 'mode':
                        run_function.value = False
                        engage_sunset_mode(light_mngr_conn, p)
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

def on(light_mngr_conn:Connection, leds:np.ndarray):
    leds[:] = bb_config['colors']['warm']
    light_mngr_conn.send(leds)

def off(light_mngr_conn:Connection, leds:np.ndarray):
    leds[:] = bb_config['colors']['black']
    light_mngr_conn.send(leds)

def color_change(light_mngr_conn:Connection, leds:np.ndarray, phrase):
    for word in phrase.split():
        if word in bb_config['colors']:
            leds[:] = bb_config['colors'][word]
            break
    light_mngr_conn.send(leds)

def increase_brightness(light_mngr_conn:Connection, leds:np.ndarray, phrase):
    amount = re.findall(r'\d+\.\d+|\d+', phrase)
    if amount:
        amount = float(amount[0])
        if amount >= 1:
            amount = amount / 100
    else:
        amount = 0.2
    leds[:] = leds * (1+amount)
    leds[leds > 255] = 255
    light_mngr_conn.send(leds)

def decrease_brightness(light_mngr_conn, leds, phrase):
    amount = re.findall(r'\d+\.\d+|\d+', phrase)
    if amount:
        amount = float(amount[0])
        if amount >= 1:
            amount = amount / 100
    else:
        amount = 0.2
    leds[:] = leds * (1-amount)
    leds[leds < 0] = 0
    light_mngr_conn.send(leds)

def engage_sunset_mode(light_mngr_conn, phrase):
    if 'sunset' in phrase:
        light_mngr_conn.send(sunset_mode)
    if 'party' in phrase:
        light_mngr_conn.send(party_mode)

def party_mode(neo_leds:NeoPixelLEDStrip, run_function:Value):
    party_colors = np.array([
        bb_config['colors']['red'],
        bb_config['colors']['orange'],
        bb_config['colors']['yellow'],
        bb_config['colors']['lime'],
        bb_config['colors']['cyan'],
        bb_config['colors']['blue'],
        bb_config['colors']['purple'],
    ])
    n_tiles = neo_leds.leds.shape[0] // party_colors.shape[0]
    remainder = neo_leds.leds.shape[0] % party_colors.shape[0]
    party_colors = np.concatenate([np.tile(party_colors, (n_tiles, 1)), party_colors[:remainder, :]])
    i = 0
    while run_function.value:
        neo_leds.leds[:] = party_colors
        party_colors = np.roll(party_colors, i)
        time.sleep(0.5)
        i = (i + 1) % party_colors.shape[0]
        neo_leds.show()

def sunset_mode(neo_leds:NeoPixelLEDStrip, run_function:Value):
    sunset_colors = np.array([
        bb_config['colors']['yellow'],
        bb_config['colors']['red'],
        bb_config['colors']['orange'],
        bb_config['colors']['pink'],
        bb_config['colors']['purple'],
    ])
    n_tiles = neo_leds.leds.shape[0] // sunset_colors.shape[0]
    remainder = neo_leds.leds.shape[0] % sunset_colors.shape[0]
    sunset_colors = np.concatenate([np.tile(sunset_colors, (n_tiles, 1)), sunset_colors[:remainder, :]])
    sig = 2
    mu = 0
    a = int(np.floor(sunset_colors.shape[0] / 2))
    b = int(np.ceil(sunset_colors.shape[0] / 2))
    x = np.array([i for i in range(a, b)])
    gaussian = np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.))) + 1
    gaussian = gaussian[:, np.newaxis]
    i = 0
    while run_function.value:
        neo_leds.leds[:] = np.multiply(sunset_colors, gaussian)
        sunset_colors = np.roll(sunset_colors, i)
        time.sleep(0.5)
        i = (i + 1) % sunset_colors.shape[0]
        neo_leds.show()


def get_audio_device(audio: pyaudio.PyAudio):
    device_index = None
    if bb_config['device'] == 'rpi':
        device_name = bb_config['audio_device']
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

def microphone(conn:Connection, is_speaking:Value, run:Value, ready:Value):
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
        while not ready.value:
            time.sleep(0.1)
        with Microphone(audio, **config) as mic:
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
