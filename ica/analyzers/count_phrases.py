#!/usr/bin/env python3
import re

import pandas as pd

import ica


class CountPhrasesArgumentParser(ica.TypedCLIArguments):
    """Additional CLI arguments specific to the count_phrases analyzer"""

    phrases: list[str]
    use_regex: bool
    case_sensitive: bool


def get_phrase_counts(
    messages_df: pd.DataFrame,
    phrases: list[str],
    all_participants: list[str],
    use_regex: bool = False,
    case_sensitive: bool = False,
) -> pd.DataFrame:
    patterns = [phrase if use_regex else re.escape(phrase) for phrase in phrases]
    flags = 0 if case_sensitive else re.IGNORECASE

    # Initialize data dictionary with total counts
    data = {
        "phrase": phrases,
        "count": [
            messages_df["text"].str.count(pattern, flags=flags).sum()
            for pattern in patterns
        ],
        "count_from_me": [
            messages_df[messages_df["is_from_me"]]["text"]
            .str.count(pattern, flags=flags)
            .sum()
            for pattern in patterns
        ],
    }

    # Add counts for each participant
    for participant in all_participants:
        participant_msgs = messages_df[
            messages_df["sender_display_name"] == participant
        ]
        data[f"count_from_{participant}"] = [
            participant_msgs["text"].str.count(pattern, flags=flags).sum()
            for pattern in patterns
        ]

    return pd.DataFrame(data).set_index("phrase")


def main() -> None:
    cli_parser = ica.get_cli_parser()
    cli_parser.add_argument("phrases", nargs="+", help="one or more phrases to count")
    cli_parser.add_argument(
        "--use-regex",
        "-r",
        action="store_true",
        help="if specified, treats phrases as regular expressions",
    )
    cli_parser.add_argument(
        "--case-sensitive",
        "-s",
        action="store_true",
        help="if specified, treats phrases as case-sensitive",
    )
    cli_args = cli_parser.parse_args(namespace=CountPhrasesArgumentParser())
    dfs = ica.get_dataframes(
        contacts=cli_args.contacts,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_people=cli_args.from_people,
    )

    all_participants = sorted(dfs.handles["display_name"].unique())
    results = get_phrase_counts(
        dfs.messages[~dfs.messages["is_reaction"]],
        phrases=cli_args.phrases,
        all_participants=all_participants,
        use_regex=cli_args.use_regex,
        case_sensitive=cli_args.case_sensitive,
    )

    ica.output_results(
        results,
        format=cli_args.format,
        output=cli_args.output,
        prettified_label_overrides={
            **{phrase: phrase for phrase in cli_args.phrases},
            **{
                f"count_from_{display_name}": f"Count From {display_name}"
                for display_name in all_participants
            },
        },
    )


if __name__ == "__main__":
    main()
