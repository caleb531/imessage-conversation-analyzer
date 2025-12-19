#!/usr/bin/env python3

import datetime
from typing import Union

import ica

# The format to use for all date strings
DATE_FORMAT = "%Y-%m-%d"


def get_first_message_date(data: ica.ConversationData) -> datetime.datetime:
    """
    Retrieve the date of the very first message sent in the conversation
    """
    # DuckDB returns datetime objects
    res = data.messages.min("datetime").fetchone()
    if not res or res[0] is None:
        # Fallback or raise error? Assuming data exists if we got here.
        # But for type safety:
        return datetime.datetime.now()
    return res[0]


def get_dates_between(
    start_date: Union[str, datetime.datetime], end_date: Union[str, datetime.datetime]
) -> list[str]:
    """
    Get all dates between (and including) the given two dates
    """
    if isinstance(start_date, str):
        start_date = datetime.datetime.strptime(start_date, DATE_FORMAT)
    if isinstance(end_date, str):
        end_date = datetime.datetime.strptime(end_date, DATE_FORMAT)

    # Ensure we are comparing dates (midnight)
    if isinstance(start_date, datetime.datetime):
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    if isinstance(end_date, datetime.datetime):
        end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    delta = end_date - start_date
    return [
        (start_date + datetime.timedelta(days=i)).strftime(DATE_FORMAT)
        for i in range(delta.days + 1)
    ]


def get_sums_by_day(data: ica.ConversationData) -> list[tuple]:
    """
    Calculate the text message sums, grouped by date
    """
    return data.messages.aggregate(
        """
        strftime(datetime, '%Y-%m-%d') as day,
        count(*) as total,
        sum(cast(is_from_me as int)) as from_me,
        sum(cast(not is_from_me as int)) as from_them
        """,
        "day",
    ).fetchall()


def get_all_message_datestrs(data: ica.ConversationData) -> list[str]:
    """
    Retrieve a list of every date for which at least one message was sent
    """
    # We can just query distinct dates
    rows = (
        data.messages.project("strftime(datetime, '%Y-%m-%d') as day")
        .distinct()
        .fetchall()
    )
    return [row[0] for row in rows]


def get_noreply_count(data: ica.ConversationData) -> int:
    """
    Generate a day-by-day breakdown of the number of messages sent where only
    one person sent messages for that day
    """
    sums = get_sums_by_day(data)
    # sums is list of (day, total, from_me, from_them)
    count = 0
    for _, total, from_me, from_them in sums:
        if (from_me == 0 and from_them > 0) or (from_me > 0 and from_them == 0):
            count += 1
    return count


def main() -> None:
    """
    Generate a summary of message and reaction counts, by person and in total,
    as well as other insightful metrics
    """
    cli_args = ica.get_cli_parser().parse_args(namespace=ica.TypedCLIArguments())
    data = ica.get_conversation_data(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    first_date = get_first_message_date(data)
    all_datestrs = get_dates_between(first_date, str(datetime.date.today()))
    message_datestrs = get_all_message_datestrs(data)

    # Calculate totals using SQL
    # We need to filter reactions for message counts

    # Messages (no reactions)
    msgs = data.messages.filter("is_reaction IS NULL")
    res = msgs.count("ROWID").fetchone()
    msg_count = res[0] if res else 0

    res = msgs.filter("is_from_me = true").count("ROWID").fetchone()
    msg_from_me = res[0] if res else 0

    res = msgs.filter("is_from_me = false").count("ROWID").fetchone()
    msg_from_them = res[0] if res else 0

    # Reactions
    reactions = data.messages.filter("is_reaction IS NOT NULL")
    res = reactions.count("ROWID").fetchone()
    reaction_count = res[0] if res else 0

    res = reactions.filter("is_from_me = true").count("ROWID").fetchone()
    reaction_from_me = res[0] if res else 0

    res = reactions.filter("is_from_me = false").count("ROWID").fetchone()
    reaction_from_them = res[0] if res else 0

    totals_map = {
        "messages": msg_count,
        "messages_from_me": msg_from_me,
        "messages_from_them": msg_from_them,
        "reactions": reaction_count,
        "reactions_from_me": reaction_from_me,
        "reactions_from_them": reaction_from_them,
        "days_messaged": len(message_datestrs),
        "days_missed": len(all_datestrs) - len(message_datestrs),
        "days_with_no_reply": get_noreply_count(data),
    }

    # Output as list of dicts
    output_data = [{"metric": k, "total": v} for k, v in totals_map.items()]

    ica.output_results(
        output_data,
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
