import os
from ckiptagger import WS, POS, NER

# Optionally set GPU device
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Load models from local directory (e.g., "./data")
ws = WS("./data", disable_cuda=False)
pos = POS("./data", disable_cuda=False)
ner = NER("./data", disable_cuda=False)

# Example sentences
sentence_list = [
    "你現在一時的同情，不是幫助，只會讓她更痛苦。",
    "因為是兩個人做的事情，有人牽著，去哪裡都可以。"
]

# Run word segmentation, POS tagging, and NER
word_splits = ws(sentence_list)
pos_tags = pos(word_splits)
named_entities = ner(word_splits)
