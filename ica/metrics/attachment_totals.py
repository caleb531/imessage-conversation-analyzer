#!/usr/bin/env python3


import pandas as pd


def analyze(dfs):

    totals_map = {
        'gifs': dfs.attachments['mime_type'].eq('image/gif').sum(),
        'videos': dfs.attachments['mime_type'].eq('video/quicktime').sum()
    }
    return pd.DataFrame({
        'type': totals_map.keys(),
        'total': totals_map.values()
    })
