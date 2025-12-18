#!/usr/bin/env python3

import emoji
import pandas as pd

import ica


class MostFrequentEmojisCLIArguments(ica.TypedCLIArguments):
    """Additional CLI arguments specific to the most_frequent_emojis analyzer"""

    result_count: int


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

    text = dfs.messages[dfs.messages["is_reaction"].eq(False)].get("text")
    # Join all messages into one large string for faster processing
    full_text = text.str.cat(sep=" ")

    # Use emoji library to find all emojis
    found_emojis = emoji.emoji_list(full_text)

    # Filter out skin tones
    skin_tones = ["🏻", "🏼", "🏽", "🏾", "🏿"]
    cleaned_emojis = []
    for item in found_emojis:
        e = item["emoji"]
        for tone in skin_tones:
            e = e.replace(tone, "")
        cleaned_emojis.append(e)

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
