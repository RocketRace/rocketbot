'''
Converts raw data into not-as-raw data
'''

import json

with open("raw_data/channel_index.json") as fp:
    markov_channels = json.load(fp)

