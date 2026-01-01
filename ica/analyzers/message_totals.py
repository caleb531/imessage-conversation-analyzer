#!/usr/bin/env python3
import datetime
from typing import Optional

import pandas as pd

import ica


def get_first_message_date(dfs: ica.DataFrameNamespace) -> pd.Timestamp:
    """
    Retrieve the date of the very first message sent in the conversation
    """
    return pd.Timestamp(dfs.messages["datetime"].min().date())


def get_sums_by_day(dfs: ica.DataFrameNamespace) -> pd.DataFrame:
    """
    Calculate the text message sums, grouped by date
    """
    if dfs.messages.empty:
        return pd.DataFrame(
            columns=pd.Index(
                ["message_count", "is_from_me", "is_from_them"], dtype="object"
            )
        ).rename_axis(index="date")
    return (
        dfs.messages.assign(message_count=1)
        .resample("D", on="datetime")
        .sum(numeric_only=True)
        .rename_axis(index="date")
        .assign(is_from_them=lambda df: df["message_count"] - df["is_from_me"])
    )


def get_days_messaged_count(sums_by_day: pd.DataFrame) -> int:
    """
    Retrieve the number of days for which at least one message was sent
    """
    return (sums_by_day["message_count"] > 0).sum()


def get_noreply_count(sums_by_day: pd.DataFrame) -> int:
    """
    Generate a day-by-day breakdown of the number of messages sent where only
    one person sent messages for that day
    """
    is_from_me = sums_by_day["is_from_me"]
    is_from_them = sums_by_day["is_from_them"]
    return len(
        sums_by_day[
            (is_from_me.eq(0) & is_from_them.gt(0))
            | (is_from_me.gt(0) & is_from_them.eq(0))
        ]
    )


def calculate_totals(
    dfs: ica.DataFrameNamespace, to_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate the totals for the given dataframes
    """
    first_message_date = get_first_message_date(dfs)
    today = pd.Timestamp(datetime.date.today())
    if to_date:
        date_upper_bound = min(today, pd.Timestamp(to_date).replace(tzinfo=None))
    else:
        date_upper_bound = today

    if pd.isna(first_message_date):
        total_days = 0
    else:
        total_days = (date_upper_bound - first_message_date).days + 1

    sums_by_day = get_sums_by_day(dfs)
    days_messaged_count = get_days_messaged_count(sums_by_day)

    messages_only = dfs.messages[~dfs.messages["is_reaction"]]
    reactions_only = dfs.messages[dfs.messages["is_reaction"]]

    totals_map = {
        "messages": len(messages_only),
        "messages_from_me": messages_only["is_from_me"].sum(),
        "messages_from_them": (~messages_only["is_from_me"]).sum(),
        "reactions": len(reactions_only),
        "reactions_from_me": reactions_only["is_from_me"].sum(),
        "reactions_from_them": (~reactions_only["is_from_me"]).sum(),
        "days_messaged": days_messaged_count,
        "days_missed": total_days - days_messaged_count,
        "days_with_no_reply": get_noreply_count(sums_by_day),
    }
    return pd.DataFrame(
        {"metric": tuple(totals_map.keys()), "total": tuple(totals_map.values())},
    ).set_index("metric")


def main() -> None:
    """
    Generate a summary of message and reaction counts, by person and in total,
    as well as other insightful metrics
    """
    cli_args = ica.get_cli_parser().parse_args(namespace=ica.TypedCLIArguments())
    dfs = ica.get_dataframes(
        contacts=cli_args.contacts,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    ica.output_results(
        calculate_totals(dfs, to_date=cli_args.to_date),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
