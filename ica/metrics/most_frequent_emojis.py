#!/usr/bin/env python3

import importlib.resources
import json

import pandas as pd

from ica.analyzer import DataFrameNamespace

# The maximum number of most frequent emojis to output in the table
EMOJI_DISPLAY_COUNT = 10


# Fetch a list of the most popular emoji on the Web to use as a basis for
# computing this metric
def get_emoji_list():
    return json.loads(
        importlib.resources.files(__package__).joinpath("emojis.json").read_text()
    )


# Output the occurrences of specific emojis
def analyze(dfs: DataFrameNamespace) -> pd.DataFrame:
    return (
        pd.DataFrame({"emoji": get_emoji_list(), "count": 0})
        .assign(
            count=lambda df: df["emoji"].apply(
                lambda emoji: dfs.messages.query("is_reaction == False")
                .get("text")
                .str.extract(f"({emoji})")
                .count()
                .item()
            )
        )
        .query("count > 0")
        .sort_values(by="count", ascending=False)
        .reset_index(drop=True)
        .head(EMOJI_DISPLAY_COUNT)
    )
