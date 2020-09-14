#!/usr/bin/env python3


import pandas as pd


def analyze(dfs):

    # Copy the messages dataframe so that we can count all "text" column values
    # by converting them to integers (always 1)
    dfs.messages['text'] = dfs.messages['text'].apply(
        pd.to_numeric, errors='coerce').isna()
    groups_by_day = dfs.messages.resample('D', on='datetime')
    sums_by_day = groups_by_day.sum()
    sums_by_day['is_from_them'] = (sums_by_day['text']
                                   - sums_by_day['is_from_me'])
    return sums_by_day
