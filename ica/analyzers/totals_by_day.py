#!/usr/bin/env python3
import pandas as pd

import ica

# The format to use for all date strings
DATE_FORMAT = "%Y-%m-%d"


def main() -> None:
    cli_args = ica.get_cli_args()
    dfs = ica.get_dataframes(contact_name=cli_args.contact_name)
    groups_by_day = (
        dfs.messages
        # Count all "text" column values by converting them to integers (always
        # 1), because resampling the DataFrame will remove all non-numeric
        # columns
        .assign(
            text=lambda df: df["text"].apply(pd.to_numeric, errors="coerce").isna()
        ).resample("D", on="datetime")
    )
    sums_by_day = groups_by_day.sum()
    # Remove 00:00:00 from date index
    sums_by_day.index = sums_by_day.index.strftime(DATE_FORMAT).rename("date")
    sums_by_day["is_from_them"] = sums_by_day["text"] - sums_by_day["is_from_me"]
    ica.output_results(sums_by_day, format=cli_args.format)


if __name__ == "__main__":
    main()
