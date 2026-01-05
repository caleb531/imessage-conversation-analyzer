#!/usr/bin/env python3
import emoji
import pandas as pd

import ica

# List of modifier characters representing the skin tones to be removed from the
# emoji list
skin_tones = {"🏻", "🏼", "🏽", "🏾", "🏿"}


class MostFrequentEmojisCLIArguments(ica.TypedCLIArguments):
    """Additional CLI arguments specific to the most_frequent_emojis analyzer"""

    result_count: int


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
        contacts=cli_args.contacts,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    # Filter out reactions as they are not part of the message text analysis
    messages = dfs.messages[~dfs.messages["is_reaction"]].copy()

    # Create a translation table to remove skin tones
    translation_table = str.maketrans("", "", "".join(skin_tones))

    def extract_emojis(text: str) -> list[str]:
        return [
            item["emoji"].translate(translation_table)
            for item in emoji.emoji_list(text)
        ]

    # Extract emojis from all messages at once
    messages["emoji"] = messages["text"].apply(extract_emojis)

    # Explode the list of emojis so each emoji has its own row
    emoji_data = messages.explode("emoji")

    # Drop rows with no emojis
    emoji_data = emoji_data.dropna(subset=["emoji"])

    # Normalize sender column for pivoting
    # We want columns for "Me" and each participant
    emoji_data["sender_column"] = emoji_data["sender_display_name"]
    emoji_data.loc[emoji_data["is_from_me"], "sender_column"] = "Me"

    # Create a pivot table of counts
    if emoji_data.empty:
        results = pd.DataFrame()
    else:
        results = pd.crosstab(emoji_data["emoji"], emoji_data["sender_column"])

    # Ensure all participants (and "Me") are represented as columns
    all_participants = sorted(dfs.handles["display_name"].unique())
    expected_cols = ["Me"] + all_participants
    results = results.reindex(columns=expected_cols, fill_value=0)

    # Rename columns to match expected output format
    results = results.rename(
        columns=lambda col: "count_from_me" if col == "Me" else f"count_from_{col}"
    )

    # Calculate total count and insert as first column
    results.insert(0, "count", results.sum(axis=1))

    # Sort by total count and take top N
    # Note: We sort by index (emoji) secondarily to ensure deterministic ordering
    # when counts are tied
    results.index.name = "emoji"
    results = (
        results.sort_values(["count", "emoji"], ascending=[False, True])
        .head(cli_args.result_count)
        .astype(int)
    )

    ica.output_results(
        results,
        format=cli_args.format,
        output=cli_args.output,
        prettified_label_overrides={
            f"count_from_{display_name}": f"Count From {display_name}"
            for display_name in all_participants
        },
    )


if __name__ == "__main__":
    main()
