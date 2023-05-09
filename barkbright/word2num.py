import re
import math

split_re = r'[-\s]'

ones_map = {
    'zero': 0,
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
}

teens_map = {
    'ten': 10,
    'eleven': 11,
    'twelve': 12,
    'thirteen': 13,
    'fourteen': 14,
    'fifteen': 15,
    'sixteen': 16,
    'seventeen': 17,
    'eighteen': 18,
    'nineteen': 19,
}

tens_map = {
    'twenty': 20,
    'thirty': 30,
    'fourty': 40,
    'fifty': 50,
    'sixty': 60,
    'seventy': 70,
    'eighty': 80,
    'ninety': 90,
}

large_map = {
    'hundred': 100,
    'thousand': 1000,
    'million': 1000000,
    'billion': 1000000000,
    'trillion': 1000000000000
}

ands_set = {'and', 'an', 'on'}

word_maps = [ones_map, teens_map, tens_map, large_map]

def word2num(phrase:str)->str:
    words = re.split(split_re, phrase)
    number_qs = [list()]
    indicies = list()
    is_num = False
    length = 0
    index = 0
    out_words = list()
    for i, word in enumerate(words):
        previous_is_num = is_num
        is_num = False
        for word_map in word_maps:
            if previous_is_num and word in ands_set:
                length += 1
                is_num = True
                break
            is_num = is_num or word in word_map
            if word in word_map:
                length += 1
                number_qs[-1].append(word_map[word])
                if index == 0:
                    index = i
        if previous_is_num and not is_num:
            indicies.append((index, length))
            number_qs.append(list())
            length = 0
            index = 0
    last = 0
    for index, number_q in zip(indicies, number_qs):
        i, length = index
        number = 0
        temp = 0
        while number_q:
            if number < number_q[-1]:
                if number != 0 and temp != 0:
                    digit = math.floor(math.log10(number))
                    number += (temp - 1) * 10**digit
                number += number_q.pop()
                temp = 0
            else:
                if temp == 0:
                    temp = number_q.pop()
                else:
                    if temp < number_q[-1]:
                        temp += number_q.pop()
                    else:
                        digit = math.floor(math.log10(temp))
                        temp += (number_q.pop() - 1) * 10**digit
        if temp != 0 and temp < number:
            digit = math.floor(math.log10(number))
            number += (temp - 1) * 10**digit
        out_words += words[last:i] + [str(int(number))]
        last = i + length
    out_words += words[last:]
    return ' '.join(out_words)

if __name__ == '__main__':
    print(word2num('i have two-hundred and thirty two apples and also I have fifteen percent more than you and also thirteen billion four hundred fifty one million four hundred thousand fifty two is a number'))
    # print(word2num('also thirteen billion four hundred fifty one million four hundred thousand fifty two is a number'))
