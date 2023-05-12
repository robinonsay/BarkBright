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
from barkbright.iot.neopixel import NeoPixelLEDStrip
from multiprocessing import Process, Pipe, Value
from multiprocessing.connection import Connection
from dataset import BB_INTENTS

def main(outdir):
    running = Value('B', True)
    ready = Value('B', False)
    parent_mic_conn, child_mic_conn = Pipe()
    prcs_mic = Process(target=microphone, args=(child_mic_conn, running, ready))
    prcs_mic.start()
    try:
        for phrase in asr.collect_data(parent_mic_conn, ready):
            print(phrase)
    finally:
        running.value = False

def microphone(conn:Connection, run:Value, ready:Value):
    with Audio() as audio:
        config = {
            'format': pyaudio.paInt16,
            'channels': 1,
            'rate': IN_RATE,
            'input': True,
            'frames_per_buffer': CHUNK_SIZE,
        }
        while not ready.value:
            time.sleep(0.1)
        print('Recording...')
        with Microphone(audio, **config) as mic:
            # print('Snooopy Listening...')
            while run.value:
                audio = mic.read(CHUNK_SIZE, exception_on_overflow=False)
                conn.send_bytes(audio)
