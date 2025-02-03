#!/usr/bin/env python3

import re

import pandas as pd

import ica


def main() -> None:

    cli_parser = ica.get_cli_parser()
    cli_parser.add_argument("phrases", nargs="+", help="one or more phrases to count")
    cli_args = cli_parser.parse_args()
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )
    filtered_messages = dfs.messages[~dfs.messages["is_reaction"]]

    ica.output_results(
        (
            pd.DataFrame(
                {
                    "phrase": cli_args.phrases,
                    "count": (
                        filtered_messages["text"]
                        .str.count(re.escape(phrase), flags=re.IGNORECASE)
                        .sum()
                        for phrase in cli_args.phrases
                    ),
                    "count_from_me": (
                        filtered_messages[filtered_messages["is_from_me"].eq(True)][
                            "text"
                        ]
                        .str.count(re.escape(phrase), flags=re.IGNORECASE)
                        .sum()
                        for phrase in cli_args.phrases
                    ),
                    "count_from_them": (
                        filtered_messages[filtered_messages["is_from_me"].eq(False)][
                            "text"
                        ]
                        .str.count(re.escape(phrase), flags=re.IGNORECASE)
                        .sum()
                        for phrase in cli_args.phrases
                    ),
                }
            ).set_index("phrase")
        ),
        format=cli_args.format,
        output=cli_args.output,
        prettify_index=False,
    )


if __name__ == "__main__":
    main()
