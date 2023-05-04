from typing import List, Tuple

CONJUNCTIONS = {
    "and",
    "then",
    "so",
}

def split_on_conj(phrase: str) -> List[str]:
    words = phrase.split()
    sub_phrases = list()
    current = list()
    for word in words:
        if word in CONJUNCTIONS:
            if current:
                sub_phrases.append(' '.join(current))
                current.clear()
        else:
            current.append(word)
    sub_phrases.append(' '.join(current))
    return sub_phrases
