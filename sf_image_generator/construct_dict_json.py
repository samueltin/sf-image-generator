import os
import json

SRC_DICT=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data',  'dict', 'full_dict.txt')
JSON_DICT=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data',  'dict', 'full_dict.json')

json_dict = {}

with open(SRC_DICT, mode='r', encoding='utf-8') as src_dict:
    content = src_dict.read()
    lines = content.split()
    for id, char in enumerate(lines):
        json_dict[char]=id

with open(JSON_DICT, 'w') as outfile:
    json.dump(json_dict, outfile)

