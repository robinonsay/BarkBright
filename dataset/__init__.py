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
    'unknown'
)
