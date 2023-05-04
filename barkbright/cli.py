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
from barkbright import parsing
from dataset import BB_INTENTS

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
    while True:
        phrase = input('[In]: ').lower()
        if phrase == '' or phrase is None:
            if phrases and intent is not None:
                for i, p in enumerate(phrases[-num_new_phrases:-1]):
                    data.append({
                        'intent': intent[i,0],
                        'phrase': p
                    })
            break
        if phrase == '<no>':
            intent = input(f"What was the intent?\nOptions:{' '.join(BB_INTENTS)}\nIn: ").lower()
            while intent not in BB_INTENTS:
                intent = input(f"Options:{' '.join(BB_INTENTS)}\nIn: ").lower()
            data.append({
                'intent': intent,
                'phrase': phrases[-1]
            })
        else:
            sub_phrases = parsing.split_on_conj(phrase)
            if phrases and intent is not None:
                for i, p in enumerate(phrases[-num_new_phrases:-1]):
                    data.append({
                        'intent': intent[i,0],
                        'phrase': p
                    })
            intent = intent_model.predict(sub_phrases, threshold=10e-3)
            for i, p in enumerate(sub_phrases):
                print(f"Intent: {intent[i,0]}\n\tConfidence: {intent[i,1]}\t Log Confidence: {10*np.log10(intent[i,1])}]")
            phrases += sub_phrases
            num_new_phrases = len(sub_phrases)
    log_name = input('Log file name [In]: ')
    log_name = '_'.join(log_name.split())
    with open(f'{log_name}', 'w') as f:
        json.dump(data,f)

