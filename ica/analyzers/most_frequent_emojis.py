#!/usr/bin/env python3

from collections import Counter
from typing import TypedDict

import emoji

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


def get_concatenated_messages(data: ica.ConversationData) -> str:
    """
    Retrieve and concatenate all non-reaction message texts into a single string.
    """
    # Filter reactions
    rows = data.messages.filter("is_reaction IS NULL").project("text").fetchall()
    # rows is list of tuples [(text,), (text,), ...]
    # Filter out None values just in case
    return " ".join(row[0] for row in rows if row[0])


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
    data = ica.get_conversation_data(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    full_text = get_concatenated_messages(data)
    found_emojis = emoji.emoji_list(full_text)
    cleaned_emojis = filter_skin_tones(found_emojis)

    # Count emojis
    counts = Counter(cleaned_emojis)

    # Get top N
    top_emojis = counts.most_common(cli_args.result_count)

    ica.output_results(
        [{"emoji": e, "count": c} for e, c in top_emojis],
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
