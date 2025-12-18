#!/usr/bin/env python3

import importlib.resources
import json
import re

import pandas as pd

import ica


class MostFrequentEmojisCLIArguments(ica.TypedCLIArguments):
    """Additional CLI arguments specific to the most_frequent_emojis analyzer"""

    result_count: int


def get_emoji_list() -> list[str]:
    """
    Fetch a list of the most popular emoji on the Web to use as a basis for
    computing this metric
    """
    return json.loads(
        importlib.resources.files("ica")
        .joinpath("data")
        .joinpath("emojis.json")
        .read_text()
    )


# Output the occurrences of specific emojis
def main() -> None:
    """
    Generates count data for the top 10 most frequently used emojis across the
    entire conversation
    """
    cli_parser = ica.get_cli_parser()
    cli_parser.add_argument(
        "--result-count",
        type=int,
        default=10,
        help="the number of emoji results to rank",
    )
    cli_args = cli_parser.parse_args(namespace=MostFrequentEmojisCLIArguments())
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    emojis = get_emoji_list()
    text = dfs.messages[dfs.messages["is_reaction"].eq(False)].get("text")
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
            .head(cli_args.result_count)
        ),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
