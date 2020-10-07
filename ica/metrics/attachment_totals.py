#!/usr/bin/env python3


import pandas as pd


def analyze(dfs):

    totals_map = {
        'gifs': dfs.attachments['mime_type'].eq('image/gif').sum(),
        'youtube_videos': (dfs.messages['text'].str.extract(
            r'(https?://(?:www\.)(?:youtube\.com|youtu\.be)/(?:.*?)(?:\s|$))')
            .drop_duplicates()
            .count()
            .item()),
        'recorded_videos': (dfs.attachments['mime_type']
                            .eq('video/quicktime').sum())
    }
    attachment_totals = pd.DataFrame({
        'type': totals_map.keys(),
        'total': totals_map.values()
    })
    return (attachment_totals
            .sort_values(by='total', ascending=False)
            .reset_index(drop=True))
