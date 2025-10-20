#!/usr/bin/env python3

import pandas as pd

import ica


def convert_bool_to_yesno(value: bool) -> str:
    """
    Convert a boolean value to "Yes"/"No"
    """
    return str(value).replace("True", "Yes").replace("False", "No")


def main() -> None:
    """
    Generates a full, unedited transcript of every message, including
    reactions, between you and the other person (attachment files not included)
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
        pd.DataFrame(
            {
                "timestamp": dfs.messages["datetime"],
                # Convert 1/0 to Yes/No
                "is_from_me": dfs.messages["is_from_me"].apply(convert_bool_to_yesno),
                "is_reaction": dfs.messages["is_reaction"].apply(convert_bool_to_yesno),
                # U+FFFC is the object replacement character, which appears as the
                # textual message for every attachment
                "message": dfs.messages["text"].replace(
                    r"\ufffc", "(attachment)", regex=True
                ),
            }
        ),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
