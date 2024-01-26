#!/usr/bin/env python3

import pandas as pd

import ica


def convert_bool_to_yesno(series: pd.Series) -> pd.Series:
    return series.apply(str).replace("True", "Yes").replace("False", "No")


# Export the entire conversation
def main() -> None:
    cli_args = ica.get_cli_args()
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name, timezone=cli_args.timezone
    )
    ica.output_results(
        pd.DataFrame(
            {
                "timestamp": dfs.messages["datetime"],
                # Convert 1/0 to Yes/No
                "is_from_me": convert_bool_to_yesno(dfs.messages["is_from_me"]),
                "is_reaction": convert_bool_to_yesno(dfs.messages["is_reaction"]),
                # U+FFFC is the object replacement character, which appears as the
                # textual message for every attachment
                "message": dfs.messages["text"].replace(
                    r"\ufffc", "(attachment)", regex=True
                ),
            }
        ),
        format=cli_args.format,
    )


if __name__ == "__main__":
    main()
