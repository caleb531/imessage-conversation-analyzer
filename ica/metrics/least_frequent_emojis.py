#!/usr/bin/env python3

import json

import pandas as pd


# The maximum number of least frequent emojis to output in the table
EMOJI_DISPLAY_COUNT = 20


# Fetch a list of the most popular emoji on the Web to use as a basis for
# computing this metric
def get_emoji_list():

    with open('ica/emojis.json', 'r') as emojis_file:
        return json.load(emojis_file)


# Output the occurrences of specific emojis
def analyze(dfs):

    emojis = get_emoji_list()
    least_frequent_emojis = pd.DataFrame({
        'emoji': emojis,
        'count': [dfs.messages['text'].str.extract('(' + emoji + ')')
                  .count().item() for emoji in emojis]
    })
    # Filter out all emojis that have never been sent
    least_frequent_emojis = least_frequent_emojis[
        (least_frequent_emojis[['count']] != 0).all(axis=1)]
    return (least_frequent_emojis
            .sort_values(by='count', ascending=True)
            .reset_index(drop=True)
            .head(EMOJI_DISPLAY_COUNT))
