import json
import numpy as np
from barkbright.models.intent import IntentMatchingModel
from dataset import BB_INTENTS

def main(train=False):
    intent_model = IntentMatchingModel()
    if train:
        intent_model.train()
        intent_model.save()
    else:
        intent_model.load()
    phrases = list()
    data = list()
    intent = None
    while True:
        phrase = input('In: ').lower()
        if phrase == '' or phrase is None:
            if phrases and intent is not None:
                data.append({
                    'intent': intent[0,0],
                    'phrase': phrases[-1]
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
            if phrases and intent is not None:
                data.append({
                    'intent': intent[0,0],
                    'phrase': phrases[-1]
                })
            intent = intent_model.predict([phrase], threshold=10e-3)
            print(f"Intent: {intent[0,0]}\tConfidence: {intent[0,1]}\t Log Confidence: {10*np.log10(intent[0,1])}]")
            phrases.append(phrase)
    print(data)
    with open('user-data.json', 'w') as f:
        json.dump(data,f)

