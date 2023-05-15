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
import os
from pathlib import Path
from datetime import datetime
from barkbright.models.intent import IntentMatchingModel
from barkbright import Audio, Speaker, Microphone, CHUNK_SIZE, bb_config, IN_RATE
from barkbright import parsing
from barkbright.word2num import word2num
from barkbright import dialogue as dlg
from barkbright.models import asr
from barkbright.iot import neopixel
from multiprocessing import Process, Pipe, Value
from multiprocessing.connection import Connection
IS_RPI = bb_config['device'] == 'rpi'
if IS_RPI:
    from RPi import GPIO

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
    fft_conn, child_fft_conn = Pipe()
    prcs_mic = Process(target=microphone, args=(child_mic_conn, child_fft_conn, is_speaking, running, ready))
    parent_speaker_conn, child_speaker_conn = Pipe()
    prcs_spkr = Process(target=speaker, args=(child_speaker_conn, is_speaking, running))
    light_mngr_conn,  child_light_mngr_conn = Pipe()
    prcs_light_mngr = Process(target=neopixel.light_manager, args=(child_light_mngr_conn, running, run_function))
    leds = np.zeros((bb_config['led_config']['count'], 3))
    prcs_shutdown = Process(target=shutdown, args=(running, ))
    try:
        prcs_light_mngr.start()
        run_function.value = False
        light_mngr_conn.send((neopixel.on, None))
        time.sleep(0.5)
        run_function.value = False
        light_mngr_conn.send((neopixel.off, None))
        prcs_mic.start()
        prcs_spkr.start()
        transition = 'root'
        reset = True
        prcs_shutdown.start()
        for phrase, is_done in asr.listen(parent_mic_conn, ready):
            if not running.value:
                break
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
                        if 'transition' in dlg.dialogue[str(transition)]:
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
                        else:
                            print(f'INVAID TRANSITION: {transition}')
                            transition = 'root'
                    if intent_str == 'on':
                        run_function.value = False
                        light_mngr_conn.send((neopixel.on, None))
                    elif intent_str == 'off':
                        run_function.value = False
                        light_mngr_conn.send((neopixel.off, None))
                    elif intent_str == 'color':
                        run_function.value = False
                        light_mngr_conn.send((neopixel.color_change, (p,)))
                    elif intent_str == 'increase':
                        run_function.value = False
                        light_mngr_conn.send((neopixel.increase_brightness, (p,)))
                    elif intent_str == 'decrease':
                        run_function.value = False
                        light_mngr_conn.send((neopixel.decrease_brightness, (p,)))
                    elif intent_str == 'mode':
                        run_function.value = False
                        if 'sunset' in p:
                            light_mngr_conn.send((neopixel.sunset_mode, None))
                        if 'party' in p:
                            light_mngr_conn.send((neopixel.party_mode, (fft_conn,)))
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

def microphone(conn:Connection, fft_conn:Connection, is_speaking:Value, run:Value, ready:Value):
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
            send_to_fft = False
            while run.value:
                if fft_conn.poll():
                    send_to_fft = fft_conn.recv()
                if record and not is_speaking.value:
                    audio = mic.read(CHUNK_SIZE, exception_on_overflow=False)
                    conn.send_bytes(audio)
                    if send_to_fft:
                        fft_conn.send_bytes(audio)
                elif record:
                    mic.stop_stream()
                    record = False
                elif not is_speaking.value:
                    mic.start_stream()
                    record = True

def shutdown(run:Value):
    if IS_RPI:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(bb_config['shutdown_pin'], GPIO.IN)
        while run.value:
            time.sleep(0.01)
            run.value = GPIO.input(bb_config['shutdown_pin']) == GPIO.LOW
        GPIO.cleanup()
        print('Shutting Down')
        os.system('sudo shutdown now')

            
        
