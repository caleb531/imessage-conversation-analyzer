#!/usr/bin/env python3

import ica

# The format to use for all date strings
DATE_FORMAT = "%Y-%m-%d"


def main() -> None:
    """
    Generates a comprehensive breakdown of message totals for every day you and
    the other person have been messaging in the conversation
    """
    cli_args = ica.get_cli_parser().parse_args(namespace=ica.TypedCLIArguments())
    data = ica.get_conversation_data(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    # Aggregate by day
    rel = data.messages.aggregate(
        """
        strftime(datetime, '%Y-%m-%d') as date,
        count(*) as "#_sent",
        sum(cast(is_from_me as int)) as "#_sent_by_me",
        sum(cast(not is_from_me as int)) as "#_sent_by_them"
        """,
        "date",
    ).order("date")

    ica.output_results(
        rel,
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
