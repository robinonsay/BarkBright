import json
import re
import random
from dataset import bb_data, BB_INTENTS, bb_data_path
from pathlib import Path
from barkbright.colors import KNOWN_COLORS
from barkbright.modes import KNOWN_MODES

seed_path = Path(__file__).parent / Path('seed.json')
with open(seed_path, 'r') as f:
    seed_data = json.load(f)

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

_postphrase = KeyWord('posephrase', [
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

_number = KeyWord('number', [str(random.randint(0,100) for i in range(25))])

_set = KeyWord('set', [
    'set',
    'adjust',
    'change'
])

_color = KeyWord('color', KNOWN_COLORS)

_mode = KeyWord('mode', KNOWN_MODES)

keywords = [_on, _off, _prephrase, _postphrase, _prep, _light, _number, _set, _color, _mode]
keyword_re = r'<\w+>'

used_phrases = {data['phrase'] for data in bb_data}

for intent in BB_INTENTS:
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
            if phrase not in used_phrases:
                bb_data.append({
                    'intent': intent,
                    'phrase': phrase
                })

with open(bb_data_path, 'w') as f:
    json.dump(bb_data, f)
    print(f'Dataset Size: {len(bb_data)}')
