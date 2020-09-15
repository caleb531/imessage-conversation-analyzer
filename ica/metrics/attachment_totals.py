#!/usr/bin/env python3


import pandas as pd


def analyze(dfs):

    totals_map = {
        'gifs': dfs.attachments['mime_type'].eq('image/gif').sum(),
        'videos': dfs.attachments['mime_type'].eq('video/quicktime').sum(),
        'links': (dfs.messages['text'].str
                  .extract('https?://(.*?)$')
                  .drop_duplicates()
                  .count()
                  .item())
    }
    attachment_totals = pd.DataFrame({
        'type': totals_map.keys(),
        'total': totals_map.values()
    })
    return (attachment_totals
            .sort_values(by='total', ascending=False)
            .reset_index(drop=True))
