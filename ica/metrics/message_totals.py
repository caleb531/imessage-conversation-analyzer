#!/usr/bin/env python3


import pandas as pd


def analyze(dfs):

    totals_map = {
        'messages': len(dfs.messages.index),
        'messages_from_me': dfs.messages['is_from_me'].eq(True).sum(),
        'messages_from_them': dfs.messages['is_from_me'].eq(False).sum()
    }
    return pd.DataFrame({
        'metric': tuple(totals_map.keys()),
        'total': tuple(totals_map.values())
    })
