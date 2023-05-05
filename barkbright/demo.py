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
import numpy as np
from datetime import datetime
from barkbright.models.intent import IntentMatchingModel
from barkbright import Audio, Speaker, Microphone
from barkbright.models import tts
from barkbright import parsing
from dataset import BB_INTENTS
from barkbright.models import asr


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
    with Audio() as audio:
        with Speaker(audio) as speaker:
            with Microphone(audio) as mic:
                for phrase in asr.listen(mic):
                    if not (phrase == '' or phrase is None):
                        sub_phrases = parsing.split_on_conj(phrase)
                        intent = intent_model.predict(sub_phrases)
                        for i, p in enumerate(sub_phrases):
                            print(f"Intent: {intent[i,0]}\n\tConfidence: {intent[i,1]}\t Log Confidence: {10*np.log10(intent[i,1])}]")
                            output_phrase = f"{intent[i,0]}."
                            tts.tts(speaker, output_phrase)
