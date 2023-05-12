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
import re
import random
import nltk
from dataset import bb_data, BB_INTENTS, bb_data_path
from pathlib import Path
from nltk.corpus import brown
nltk.download('brown')

unknown_text = list()

for sent in brown.sents():
    s = ' '.join(sent)
    s = re.sub(r'[^0-9A-Za-z\s]', '', s)
    s = re.sub(r'\s{2,}', '', s)
    unknown_text.append(s.lower())

seed_path = Path(__file__).parent / Path('seed.json')
with open(seed_path, 'r') as f:
    seed_data = json.load(f)
seed_data['unknown'] += unknown_text

class KeyWord:

    def __init__(self, keyword, syns) -> None:
        self._keyword = f'<{keyword}>'
        self._syns = syns
    
    @property
    def keyword(self):
        return self._keyword

    @property
    def synonyms(self):
        return self._syns

_on = KeyWord('on', [
    'turn on',
    'activate',
    'enable'
])

_off = KeyWord('off', [
    'turn off',
    'deactivate',
    'disable'
])

_prephrase = KeyWord('prephrase', [
    'i would like to',
    'i want to',
    'i need to',
    'could you',
    'would you',
    'could you please',
    'would you please',
    'please',
])

_postphrase = KeyWord('postphrase', [
    'please',
    'thank you'
])

_prep = KeyWord('prep', [
    'the',
    'my',
    'our',
    'your',
    'her',
    'his',
    'their'
])

_light = KeyWord('light', [
    'light',
    'lights',
    'leds'
])

_number = KeyWord('number', ['55'])

_set = KeyWord('set', [
    'set',
    'adjust',
    'change',
    'make',
    'turn'
])

_color = KeyWord('color', ['red'])

_mode = KeyWord('mode', ['party'])

keywords = [_on, _off, _prephrase, _postphrase, _prep, _light, _number, _set, _color, _mode]
keyword_re = r'<\w+>'

# used_phrases = {data['phrase'] for data in bb_data}

for intent in BB_INTENTS:
    print(intent)
    for seed in seed_data[intent]:
        queue = [seed]
        phrases = list()
        while queue:
            phrase = str(queue.pop(0))
            if '<' in phrase:
                for keyword in keywords:
                    if keyword.keyword in phrase:
                        for syn in keyword.synonyms:
                            new = phrase.replace(keyword.keyword, syn)
                            queue.append(new)
            else:
                phrases.append(phrase)
        for phrase in phrases:
            bb_data.append({
                'intent': intent,
                'phrase': phrase
            })

with open(bb_data_path, 'w') as f:
    json.dump(bb_data, f, indent=4)
    print(f'Dataset Size: {len(bb_data)}')
