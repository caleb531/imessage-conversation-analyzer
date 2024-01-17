#!/usr/bin/env python3

import json
import importlib.resources

import pandas as pd


# The maximum number of most frequent emojis to output in the table
EMOJI_DISPLAY_COUNT = 10


# Fetch a list of the most popular emoji on the Web to use as a basis for
# computing this metric
def get_emoji_list():
    return json.loads(importlib.resources.files(__package__)
                      .joinpath('emojis.json').read_text())


# Output the occurrences of specific emojis
def analyze(dfs):

    emojis = get_emoji_list()
    emoji_counts = pd.DataFrame({
        'emoji': emojis,
        'count': [dfs.messages['text'].str.extract('(' + emoji + ')')
                  .count().item() for emoji in emojis]
    })
    return (emoji_counts[emoji_counts['count'] > 0]
            .sort_index(ascending=True)
            .sort_values(by='count', ascending=False)
            .reset_index(drop=True)
            .head(EMOJI_DISPLAY_COUNT))
