#!/usr/bin/env python3
import pandas as pd

import ica

# The format to use for all date strings
DATE_FORMAT = "%Y-%m-%d"


def main() -> None:
    cli_args = ica.get_cli_args()
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name, timezone=cli_args.timezone
    )
    ica.output_results(
        (
            dfs.messages
            # Count all "text" column values by converting them to integers
            # (always 1), because resampling the DataFrame will remove all
            # non-numeric columns
            .assign(
                text=lambda df: df["text"].apply(pd.to_numeric, errors="coerce").isna()
            )
            .resample("D", on="datetime")
            .sum()
            .pipe(lambda df: df.rename_axis("date", axis=0))
            .assign(is_from_them=lambda df: df["text"] - df["is_from_me"])
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
    )


if __name__ == "__main__":
    main()
