#!/usr/bin/env python3
import pandas as pd

import ica
from ica import assign_lambda, pipe_lambda

# The format to use for all date strings
DATE_FORMAT = "%Y-%m-%d"


def main() -> None:
    """
    Generates a comprehensive breakdown of message totals for every day you and
    the other person have been messaging in the conversation
    """
    cli_args = ica.get_cli_args()
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name, timezone=cli_args.timezone
    )
    ica.output_results(
        (
            dfs.messages[["text", "is_from_me", "datetime", "is_reaction"]]
            # Count all "text" column values by converting them to integers
            # (always 1), because resampling the DataFrame will remove all
            # non-numeric columns
            .assign(
                text=assign_lambda(
                    lambda df: df["text"].apply(pd.to_numeric, errors="coerce").isna()
                )
            )
            .resample("D", on="datetime")
            .sum()
            .rename_axis("date", axis="index")
            # Filter out any rows for dates where neither person sent a message
            .pipe(pipe_lambda(lambda df: df[df["text"] != 0]))
            # Add a column for the by-day number of messages from the other
            # person, for convenience (even though it can technically be derived
            # from the existing columns)
            .assign(
                is_from_them=assign_lambda(lambda df: df["text"] - df["is_from_me"])
            )
            # Do not include reaction data for brevity
            .drop(columns=["is_reaction"])
            # Rename columns to be more intuitive
            .rename(
                columns={
                    "text": "#_sent",
                    "is_from_me": "#_sent_by_me",
                    "is_from_them": "#_sent_by_them",
                }
            )
        ),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
