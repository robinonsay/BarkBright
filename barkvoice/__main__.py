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

from TTS.api import TTS
from barkbright import dialogue
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(prog='BarkBright',
                                 description='Voice Enabled LED Light Control')
parser.add_argument('-p', '--path', nargs=1)
args = parser.parse_args()

if args.path:
    OUT_PATH = args.path
else:
    OUT_PATH = Path(__file__).parent / Path('sounds')
dialogue.load_dialogue()
tts_engine = TTS(model_name='tts_models/en/vctk/vits')
for node, value in dialogue.dialogue.items():
    for i, phrase in enumerate(value['dialogue'].splitlines()):
        tts_engine.tts_to_file(text=phrase,
                            speaker='p255',
                            file_path=str(OUT_PATH / f"{node}_{i}.wav"))
