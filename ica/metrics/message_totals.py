#!/usr/bin/env python3

import datetime

import pandas as pd


# Get all dates between (and including) the given two dates
def get_dates_between(start_date, end_date):

    delta = end_date - start_date
    dates = []
    for d in range(delta.days + 1):
        date = start_date + datetime.timedelta(days=d)
        dates.append(date)
    return dates


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
