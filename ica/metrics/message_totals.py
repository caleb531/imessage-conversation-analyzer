#!/usr/bin/env python3

import datetime

import pandas as pd

# The format to use for all date strings
DATE_FORMAT = "%Y-%m-%d"


# Retrieve the date of the very first message sent in the conversation
def get_first_message_date(dfs):
    datestr = str(dfs.messages["datetime"].min().strftime(DATE_FORMAT))
    return datetime.datetime.strptime(datestr, DATE_FORMAT)


# Get all dates between (and including) the given two dates
def get_dates_between(start_date, end_date):
    return list(pd.date_range(start_date, end_date).strftime(DATE_FORMAT))


# Get all dates sent
def get_all_message_datestrs(dfs):
    groups_by_day = dfs.messages.resample("D", on="datetime")
    sums_by_day = groups_by_day.count()
    sums_by_day.index = sums_by_day.index.strftime(DATE_FORMAT)
    return list(sums_by_day.index)


# Get the number of messages with no reply (i.e. only one message sent for that
# day)
def get_noreply_count(dfs):
    # Count all "text" column values by converting them to integers (always 1),
    # because resampling the DataFrame will remove all non-numeric columns
    dfs.messages["text"] = (
        dfs.messages["text"].apply(pd.to_numeric, errors="coerce").isna()
    )
    groups_by_day = dfs.messages.resample("D", on="datetime")
    sums_by_day = groups_by_day.sum()
    sums_by_day["is_from_them"] = sums_by_day["text"] - sums_by_day["is_from_me"]
    return (
        sums_by_day["is_from_them"].eq(0).sum() + sums_by_day["is_from_me"].eq(0).sum()
    )


# Return a list of all dates in Date List B which are not in Date List A
def get_missing_datestrs(date_list_a, date_list_b):
    return sorted(set(date_list_a) - set(date_list_b))


def analyze(dfs):
    all_datestrs = get_dates_between(
        get_first_message_date(dfs), str(datetime.date.today())
    )
    message_datestrs = get_all_message_datestrs(dfs)

    totals_map = {
        "messages": len(dfs.messages.index),
        "messages_from_me": dfs.messages["is_from_me"].eq(True).sum(),
        "messages_from_them": dfs.messages["is_from_me"].eq(False).sum(),
        "days_messaged": len(message_datestrs),
        "days_missed": len(all_datestrs) - len(message_datestrs),
        "days_with_no_reply": get_noreply_count(dfs),
    }
    return pd.DataFrame(
        {"metric": tuple(totals_map.keys()), "total": tuple(totals_map.values())}
    )
