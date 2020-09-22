#!/usr/bin/env python3

import json

import pandas as pd


# The maximum number of most frequent emojis to output in the table
EMOJI_DISPLAY_COUNT = 10


# Fetch a list of the most popular emoji on the Web to use as a basis for
# computing this metric
def get_emoji_list():

    with open('ica/emojis.json', 'r') as emojis_file:
        return json.load(emojis_file)


# Output the occurrences of specific emojis
def analyze(dfs):

    emojis = get_emoji_list()
    most_frequent_emojis = pd.DataFrame({
        'emoji': emojis,
        'count': [dfs.messages['text'].str.extract('(' + emoji + ')')
                  .count().item() for emoji in emojis]
    })
    return (most_frequent_emojis
            .sort_values(by='count', ascending=False)
            .reset_index(drop=True)
            .head(EMOJI_DISPLAY_COUNT))
