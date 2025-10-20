#!/usr/bin/env python3

import re
import typing

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
) -> typing.Generator[int, None, None]:
    return (
        messages_df["text"]
        .str.count(
            re.escape(phrase) if use_regex else phrase,
            flags=re.IGNORECASE if not case_sensitive else 0,
        )
        .sum()
        for phrase in phrases
    )


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
    filtered_messages = dfs.messages[~dfs.messages["is_reaction"]]

    ica.output_results(
        (
            pd.DataFrame(
                {
                    "phrase": cli_args.phrases,
                    "count": get_phrase_counts(
                        filtered_messages,
                        cli_args.phrases,
                        case_sensitive=cli_args.case_sensitive,
                    ),
                    "count_from_me": get_phrase_counts(
                        filtered_messages[filtered_messages["is_from_me"].eq(True)],
                        cli_args.phrases,
                    ),
                    "count_from_them": get_phrase_counts(
                        filtered_messages[filtered_messages["is_from_me"].eq(False)],
                        cli_args.phrases,
                    ),
                }
            ).set_index("phrase")
        ),
        format=cli_args.format,
        output=cli_args.output,
        prettify_index=False,
    )


if __name__ == "__main__":
    main()
