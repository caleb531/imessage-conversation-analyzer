#!/usr/bin/env python3


import pandas as pd

# The format to use for all date strings
DATE_FORMAT = "%Y-%m-%d"


def analyze(dfs):
    # Count all "text" column values by converting them to integers (always 1),
    # because resampling the DataFrame will remove all non-numeric columns
    dfs.messages["text"] = (
        dfs.messages["text"].apply(pd.to_numeric, errors="coerce").isna()
    )
    groups_by_day = dfs.messages.resample("D", on="datetime")
    sums_by_day = groups_by_day.sum()
    # Remove 00:00:00 from date index
    sums_by_day.index = sums_by_day.index.strftime(DATE_FORMAT)
    sums_by_day.index = sums_by_day.index.rename("date")
    sums_by_day["is_from_them"] = sums_by_day["text"] - sums_by_day["is_from_me"]
    return sums_by_day
