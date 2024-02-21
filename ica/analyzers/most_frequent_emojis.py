#!/usr/bin/env python3

import importlib.resources
import json
import re

import pandas as pd

import ica

# The maximum number of most frequent emojis to output in the table
EMOJI_DISPLAY_COUNT = 10


def get_emoji_list() -> list[str]:
    """
    Fetch a list of the most popular emoji on the Web to use as a basis for
    computing this metric
    """
    return json.loads(
        importlib.resources.files(__package__).joinpath("emojis.json").read_text()
    )


# Output the occurrences of specific emojis
def main() -> None:
    """
    Generates count data for the top 10 most frequently used emojis across the
    entire conversation
    """
    cli_args = ica.get_cli_args()
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name, timezone=cli_args.timezone
    )
    emojis = get_emoji_list()
    text = dfs.messages.query("is_reaction == False").get("text")
    emoji_patt = re.compile(
        f"({'|'.join(re.escape(emoji) for emoji in reversed(emojis))})"
    )
    matches = (
        text.str.findall(emoji_patt).apply(pd.Series).stack().reset_index(drop=True)
    )
    ica.output_results(
        (
            pd.DataFrame({"emoji": matches.value_counts()})
            .rename({"emoji": "count"}, axis="columns")
            .rename_axis("emoji", axis="index")
            .head(EMOJI_DISPLAY_COUNT)
        ),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
