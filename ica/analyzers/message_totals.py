#!/usr/bin/env python3

import datetime
from typing import Union

import polars as pl

import ica

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
    # Polars doesn't have a direct equivalent to pd.date_range that returns a list
    # of strings so we use a range and map it
    if isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, DATE_FORMAT)
    if isinstance(end_date, str):
        end_date = datetime.datetime.strptime(end_date, DATE_FORMAT)

    delta = end_date - start_date
    return [
        (start_date + datetime.timedelta(days=i)).strftime(DATE_FORMAT)
        for i in range(delta.days + 1)
    ]


def get_sums_by_day(dfs: ica.DataFrameNamespace) -> pl.DataFrame:
    """
    Calculate the text message sums, grouped by date
    """
    return (
        dfs.messages.with_columns(
            # Create a dummy column for counting
            count=pl.lit(1)
        )
        .group_by_dynamic("datetime", every="1d")
        .agg(
            pl.col("count").sum().alias("text"),
            pl.col("is_from_me").sum().alias("is_from_me"),
        )
        .with_columns(is_from_them=pl.col("text") - pl.col("is_from_me"))
        .sort("datetime")
    )


def get_all_message_datestrs(dfs: ica.DataFrameNamespace) -> list[str]:
    """
    Retrieve a list of every date for which at least one message was sent
    """
    sums_by_day = get_sums_by_day(dfs)
    return (
        sums_by_day.filter(pl.col("text") > 0)["datetime"]
        .dt.strftime(DATE_FORMAT)
        .to_list()
    )


def get_noreply_count(dfs: ica.DataFrameNamespace) -> int:
    """
    Generate a day-by-day breakdown of the number of messages sent where only
    one person sent messages for that day
    """
    sums_by_day = get_sums_by_day(dfs)
    return sums_by_day.filter(
        (pl.col("is_from_me") == 0) & (pl.col("is_from_them") > 0)
        | (pl.col("is_from_me") > 0) & (pl.col("is_from_them") == 0)
    ).height


def main() -> None:
    """
    Generate a summary of message and reaction counts, by person and in total,
    as well as other insightful metrics
    """
    cli_args = ica.get_cli_parser().parse_args(namespace=ica.TypedCLIArguments())
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    all_datestrs = get_dates_between(
        get_first_message_date(dfs), str(datetime.date.today())
    )
    message_datestrs = get_all_message_datestrs(dfs)

    # Filter out reactions for message counts
    messages_no_reactions = dfs.messages.filter(~pl.col("is_reaction"))
    reactions_only = dfs.messages.filter(pl.col("is_reaction"))

    totals_map = {
        "messages": messages_no_reactions.height,
        "messages_from_me": (messages_no_reactions.filter(pl.col("is_from_me")).height),
        "messages_from_them": (
            messages_no_reactions.filter(~pl.col("is_from_me")).height
        ),
        "reactions": reactions_only.height,
        "reactions_from_me": (reactions_only.filter(pl.col("is_from_me")).height),
        "reactions_from_them": (reactions_only.filter(~pl.col("is_from_me")).height),
        "days_messaged": len(message_datestrs),
        "days_missed": len(all_datestrs) - len(message_datestrs),
        "days_with_no_reply": get_noreply_count(dfs),
    }
    ica.output_results(
        pl.DataFrame(
            {"metric": list(totals_map.keys()), "total": list(totals_map.values())},
        ),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
