import subprocess
from barkbright import bb_config

def speak(phrase: str):
    subprocess.run([
        'espeak',
        '-s', str(bb_config['espeak_config']['speed']),
        '-p', str(bb_config['espeak_config']['pitch']),
        '-v', str(bb_config['espeak_config']['voice']),
        phrase
    ])
