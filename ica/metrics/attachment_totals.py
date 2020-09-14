#!/usr/bin/env python3


import pandas as pd


def analyze(dfs):

    return pd.DataFrame({
        'gifs': dfs.attachments['mime_type'].eq('image/gif').sum(),
        'videos': dfs.attachments['mime_type'].eq('video/quicktime').sum()
    })
