#!/usr/bin/env python3

import re

import pandas as pd

import ica


def main() -> None:

    cli_args = ica.get_cli_args()
    phrases = cli_args.args
    if not phrases:
        raise Exception("Must provide at least one phrase to count")
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
                        .str.count(rf"\b{re.escape(phrase)}\b", flags=re.IGNORECASE)
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
