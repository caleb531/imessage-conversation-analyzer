#!/usr/bin/env python3

import datetime
from typing import Union

import pandas as pd

import ica
from ica import assign_lambda

# The format to use for all date strings
DATE_FORMAT = "%Y-%m-%d"


def get_first_message_date(dfs: ica.DataFrameNamespace) -> datetime.datetime:
    """
    Retrieve the date of the very first message sent in the conversation
    """
    datestr = str(dfs.messages["datetime"].min().strftime(DATE_FORMAT))
    return datetime.datetime.strptime(datestr, DATE_FORMAT)


def get_dates_between(
    start_date: Union[str, datetime.datetime], end_date: Union[str, datetime.datetime]
) -> list[datetime.datetime]:
    """
    Get all dates between (and including) the given two dates; each date can be
    either of type str or datetime
    """
    return list(pd.date_range(start_date, end_date).strftime(DATE_FORMAT))


def get_sums_by_day(dfs: ica.DataFrameNamespace) -> pd.DataFrame:
    """
    Calculate the text message sums, grouped by date
    """
    return (
        dfs.messages
        # Count all "text" column values by converting them to integers (always
        # 1), because resampling the DataFrame will remove all non-numeric
        # columns
        .assign(
            text=assign_lambda(
                lambda df: df["text"].apply(pd.to_numeric, errors="coerce").isna()
            )
        )
        .resample("D", on="datetime")
        .sum()
        .rename_axis("date", axis="index")
        .assign(is_from_them=assign_lambda(lambda df: df["text"] - df["is_from_me"]))
    )


def get_all_message_datestrs(dfs: ica.DataFrameNamespace) -> list[str]:
    """
    Retrieve a list of every date for which at least one message was sent
    """
    sums_by_day = get_sums_by_day(dfs)
    return list(sums_by_day.query("text > 0").index)


def get_noreply_count(dfs: ica.DataFrameNamespace) -> int:
    """
    Generate a day-by-day breakdown of the number of messages sent where only
    one person sent messages for that day
    """
    sums_by_day = get_sums_by_day(dfs)
    return len(
        sums_by_day.query(
            "(is_from_me == 0 and is_from_them > 0) or "
            "(is_from_me > 0 and is_from_them == 0)"
        )
    )


def main() -> None:
    """
    Generate a summary of message and reaction counts, by person and in total,
    as well as other insightful metrics
    """
    cli_args = ica.get_cli_args()
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name, timezone=cli_args.timezone
    )

    all_datestrs = get_dates_between(
        get_first_message_date(dfs), str(datetime.date.today())
    )
    message_datestrs = get_all_message_datestrs(dfs)

    totals_map = {
        "messages": len(dfs.messages.query("is_reaction == False")),
        "messages_from_me": (
            dfs.messages.query("is_reaction == False")["is_from_me"].eq(True).sum()
        ),
        "messages_from_them": (
            dfs.messages.query("is_reaction == False")["is_from_me"].eq(False).sum()
        ),
        "reactions": len(dfs.messages.query("is_reaction == True")),
        "reactions_from_me": (
            dfs.messages.query("is_reaction == True")["is_from_me"].eq(True).sum()
        ),
        "reactions_from_them": (
            dfs.messages.query("is_reaction == True")["is_from_me"].eq(False).sum()
        ),
        "days_messaged": len(message_datestrs),
        "days_missed": len(all_datestrs) - len(message_datestrs),
        "days_with_no_reply": get_noreply_count(dfs),
    }
    ica.output_results(
        pd.DataFrame(
            {"metric": tuple(totals_map.keys()), "total": tuple(totals_map.values())},
        ).set_index("metric"),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
