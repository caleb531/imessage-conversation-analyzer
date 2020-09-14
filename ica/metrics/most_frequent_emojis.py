#!/usr/bin/env python3

import pandas as pd


# The respective emojis to count across the entire iMessage conversation
EMOJIS = ('❤️', '😍', '😘', '🥰', '😊', '😂', '😅', '🌙')


def analyze(dfs):

    # Output the occurrences of specific emojis
    most_frequent_emojis = pd.DataFrame({
        'emoji': EMOJIS,
        'count': [dfs.messages['text'].str.extract('(' + emoji + ')')
                  .count().item() for emoji in EMOJIS]
    })

    return most_frequent_emojis.sort_values(by='count', ascending=False)
