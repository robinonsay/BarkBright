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
from pathlib import Path

bb_data_path = Path(__file__).parent / Path('dataset.json')

with open(bb_data_path, 'r') as f:
    bb_data = json.load(f)

BB_INTENTS = (
    'on',
    'off',
    'increase',
    'decrease',
    'color',
    'mode',
    'unknown',
    'sleep'
)
