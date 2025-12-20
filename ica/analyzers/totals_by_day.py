#!/usr/bin/env python3
import polars as pl

import ica

# The format to use for all date strings
DATE_FORMAT = "%Y-%m-%d"


def main() -> None:
    """
    Generates a comprehensive breakdown of message totals for every day you and
    the other person have been messaging in the conversation
    """
    cli_args = ica.get_cli_parser().parse_args(namespace=ica.TypedCLIArguments())
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )
    ica.output_results(
        (
            dfs.messages.select(["text", "is_from_me", "datetime", "is_reaction"])
            .with_columns(count=pl.lit(1))
            .group_by_dynamic("datetime", every="1d")
            .agg(
                pl.col("count").sum().alias("text"),
                pl.col("is_from_me").sum().alias("is_from_me"),
            )
            # Filter out any rows for dates where neither person sent a message
            .filter(pl.col("text") != 0)
            # Add a column for the by-day number of messages from the other
            # person, for convenience
            .with_columns(is_from_them=pl.col("text") - pl.col("is_from_me"))
            # Rename columns to be more intuitive
            .rename(
                {
                    "datetime": "date",
                    "text": "#_sent",
                    "is_from_me": "#_sent_by_me",
                    "is_from_them": "#_sent_by_them",
                }
            )
            .sort("date")
        ),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
