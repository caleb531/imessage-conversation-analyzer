#!/usr/bin/env python3

import importlib.resources
import json
import re

import pandas as pd

import ica
from ica import assign_lambda

# The maximum number of most frequent emojis to output in the table
EMOJI_DISPLAY_COUNT = 10


# Fetch a list of the most popular emoji on the Web to use as a basis for
# computing this metric
def get_emoji_list() -> list[str]:
    return json.loads(
        importlib.resources.files(__package__).joinpath("emojis.json").read_text()
    )


# Output the occurrences of specific emojis
def main() -> None:
    cli_args = ica.get_cli_args()
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name, timezone=cli_args.timezone
    )
    ica.output_results(
        (
            pd.DataFrame({"emoji": get_emoji_list(), "count": 0})
            .assign(
                count=assign_lambda(
                    lambda df: df["emoji"].apply(
                        lambda emoji: dfs.messages.query("is_reaction == False")
                        .get("text")
                        # A few emoji, like *️⃣, are regex special characters with
                        # combining characters added to make them emoji; however,
                        # because they are fundamentally regex special characters,
                        # they will break the regex syntax unless escaped
                        .str.count(re.escape(emoji))
                        .sum()
                    )
                )
            )
            .query("count > 0")
            .sort_values(by="count", ascending=False)
            .reset_index(drop=True)
            .set_index("emoji")
            .head(EMOJI_DISPLAY_COUNT)
        ),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
