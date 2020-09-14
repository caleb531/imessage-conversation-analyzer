#!/usr/bin/env python3

import collections
import pandas as pd


# Fetch a list of the most popular emoji on the Web to use as a basis for
# computing this metric
def get_emoji_list():

    with open('ica/emojis.txt', 'r', encoding='utf-8') as emojis_file:
        # Filter out duplicates
        return tuple(collections.OrderedDict.fromkeys(emojis_file.read()))


# Output the occurrences of specific emojis
def analyze(dfs):

    emojis = get_emoji_list()
    print(emojis)
    return
    most_frequent_emojis = pd.DataFrame({
        'emoji': emojis,
        'count': [dfs.messages['text'].str.extract('(' + emoji + ')')
                  .count().item() for emoji in emojis]
    })
    return most_frequent_emojis.sort_values(by='count', ascending=False)
