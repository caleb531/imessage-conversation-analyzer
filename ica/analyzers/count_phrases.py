#!/usr/bin/env python3

import re

import pandas as pd

import ica


def main() -> None:

    cli_parser = ica.get_cli_parser()
    cli_parser.add_argument("phrases", nargs="+", help="one or more phrases to count")
    cli_args = cli_parser.parse_args()
    phrases = cli_args.phrases
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name, timezone=cli_args.timezone
    )
    filtered_messages = dfs.messages[~dfs.messages["is_reaction"]]
    ica.output_results(
        (
            pd.DataFrame(
                {
                    "phrase": phrases,
                    "count": (
                        filtered_messages["text"]
                        .str.count(re.escape(phrase), flags=re.IGNORECASE)
                        .sum()
                        for phrase in phrases
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
