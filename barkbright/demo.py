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
import json
import numpy as np
from datetime import datetime
from barkbright.models.intent import IntentMatchingModel
from barkbright import Audio, Speaker, Microphone, CHIME_PATH
from barkbright import parsing
from dataset import BB_INTENTS
from barkbright.models import asr
from barkbright.iot.neopixel import NeoPixelLEDStrip, LED_COUNT
from barkbright.colors import COLOR_MAP

def main(train=False):
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

    with Audio() as audio, Speaker(audio) as speaker, Microphone(audio) as mic, NeoPixelLEDStrip(LED_COUNT) as np_leds, wave.open(CHIME_PATH, 'rb') as chime:
        for phrase in asr.listen(mic):
            while len(data := chime.readframes(1024)):
                speaker.write(data)
            if not (phrase == '' or phrase is None):
                sub_phrases = parsing.split_on_conj(phrase)
                intent = intent_model.predict(sub_phrases)
                for i, p in enumerate(sub_phrases):
                    print(f"Intent: {intent[i,0]}\n\tConfidence: {intent[i,1]}\t Log Confidence: {10*np.log10(intent[i,1])}]")
                    intent_str = intent[i,0]
                    if intent_str == 'on':
                        np_leds[:] = COLOR_MAP['white']
                    elif intent_str == 'off':
                        np_leds[:] = COLOR_MAP['black']
                    elif intent_str == 'color':
                        words = p.split()
                        for word in words:
                            if word in COLOR_MAP:
                                np_leds[:] = COLOR_MAP[word]
