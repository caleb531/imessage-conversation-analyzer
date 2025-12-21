#!/usr/bin/env python3

import re

import pandas as pd

import ica


class CountPhrasesArgumentParser(ica.TypedCLIArguments):
    """Additional CLI arguments specific to the count_phrases analyzer"""

    phrases: list[str]
    use_regex: bool
    case_sensitive: bool


# class CountPhrasesArgumentParser(ica.ICAArgumentParser):
#     pass


def get_phrase_counts(
    messages_df: pd.DataFrame,
    phrases: list[str],
    use_regex: bool = False,
    case_sensitive: bool = False,
) -> pd.DataFrame:
    patterns = [phrase if use_regex else re.escape(phrase) for phrase in phrases]
    flags = 0 if case_sensitive else re.IGNORECASE

    # Filter dataframes once to avoid repeated filtering in the loop
    messages_from_me = messages_df[messages_df["is_from_me"]]
    messages_from_them = messages_df[~messages_df["is_from_me"]]

    return pd.DataFrame(
        {
            "phrase": phrases,
            "count": (
                messages_df["text"].str.count(pattern, flags=flags).sum()
                for pattern in patterns
            ),
            "count_from_me": (
                messages_from_me["text"].str.count(pattern, flags=flags).sum()
                for pattern in patterns
            ),
            "count_from_them": (
                messages_from_them["text"].str.count(pattern, flags=flags).sum()
                for pattern in patterns
            ),
        }
    ).set_index("phrase")


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
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    ica.output_results(
        get_phrase_counts(
            dfs.messages[~dfs.messages["is_reaction"]],
            phrases=cli_args.phrases,
            use_regex=cli_args.use_regex,
            case_sensitive=cli_args.case_sensitive,
        ),
        format=cli_args.format,
        output=cli_args.output,
        prettify_index=False,
    )


if __name__ == "__main__":
    main()
