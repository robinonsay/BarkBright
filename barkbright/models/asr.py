import pyaudio
import json
from vosk import Model, KaldiRecognizer
from pathlib import Path

MODEL_PATH = Path('barkbright/models/assets/vosk-model-small-en-us-0.15')

def listen(model_path=None, rate=16000, chunk=1024, device_index=None) -> str:
    model = model_path if model_path else Model(model_path=MODEL_PATH.as_posix())
    recognizer = KaldiRecognizer(model, rate)
    recognizer.SetWords(True)
    recognizer.SetPartialWords(True)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk,
                    input_device_index=device_index)
    try:
        while True:
            data = stream.read(chunk, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                print(result['text'])
                yield result['text']
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
