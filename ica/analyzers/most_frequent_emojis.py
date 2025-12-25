#!/usr/bin/env python3

from typing import TypedDict

import emoji
import pandas as pd

import ica

# List of modifier characters representing the skin tones to be removed from the
# emoji list
skin_tones = {"🏻", "🏼", "🏽", "🏾", "🏿"}


class MostFrequentEmojisCLIArguments(ica.TypedCLIArguments):
    """Additional CLI arguments specific to the most_frequent_emojis analyzer"""

    result_count: int


class EmojiMatch(TypedDict):
    """Type definition for the dictionary returned by emoji.emoji_list()"""

    emoji: str
    match_start: int
    match_end: int


def get_concatenated_messages(messages: pd.DataFrame) -> str:
    """
    Retrieve and concatenate all non-reaction message texts into a single string.
    """
    text = messages[messages["is_reaction"].eq(False)].get("text")
    return text.str.cat(sep=" ")


def filter_skin_tones(found_emojis: list[EmojiMatch]) -> list[str]:
    """
    Extract emojis from the emoji_list result and strip skin tone modifiers.
    """
    # str.maketrans(x, y, z) creates a translation table. The first two
    # arguments are for mapping characters (x -> y). The third argument (z)
    # specifies characters to delete. Here, we pass empty strings for x and y
    # because we don't want to replace anything, only delete the skin tone
    # characters provided in the third argument.
    translation_table = str.maketrans("", "", "".join(skin_tones))
    return [item["emoji"].translate(translation_table) for item in found_emojis]


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
        contact=cli_args.contact,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    full_text = get_concatenated_messages(dfs.messages)
    found_emojis = emoji.emoji_list(full_text)
    cleaned_emojis = filter_skin_tones(found_emojis)

    ica.output_results(
        (
            pd.DataFrame({"emoji": pd.Series(cleaned_emojis).value_counts()})
            .rename({"emoji": "count"}, axis="columns")
            .rename_axis("emoji", axis="index")
            .head(cli_args.result_count)
        ),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
