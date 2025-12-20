#!/usr/bin/env python3

import re
import typing

import polars as pl

import ica


class CountPhrasesArgumentParser(ica.TypedCLIArguments):
    """Additional CLI arguments specific to the count_phrases analyzer"""

    phrases: list[str]
    use_regex: bool
    case_sensitive: bool


# class CountPhrasesArgumentParser(ica.ICAArgumentParser):
#     pass


def get_phrase_counts(
    messages_df: pl.DataFrame,
    phrases: list[str],
    use_regex: bool = False,
    case_sensitive: bool = False,
) -> typing.Generator[int, None, None]:
    for phrase in phrases:
        pattern = re.escape(phrase) if not use_regex else phrase
        if not case_sensitive:
            # Polars regex is case-sensitive by default. To make it case-insensitive,
            # we can use the (?i) flag at the start of the pattern if using regex,
            # or lowercase both if not using regex (but str.count_matches uses regex
            # under the hood)
            # The easiest way for case-insensitive regex in Polars is usually (?i)
            pattern = f"(?i){pattern}"

        yield messages_df["text"].str.count_matches(pattern).sum()


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
    filtered_messages = dfs.messages.filter(~pl.col("is_reaction"))

    ica.output_results(
        (
            pl.DataFrame(
                {
                    "phrase": cli_args.phrases,
                    "count": get_phrase_counts(
                        filtered_messages,
                        cli_args.phrases,
                        use_regex=cli_args.use_regex,
                        case_sensitive=cli_args.case_sensitive,
                    ),
                    "count_from_me": get_phrase_counts(
                        filtered_messages.filter(pl.col("is_from_me")),
                        cli_args.phrases,
                        use_regex=cli_args.use_regex,
                        case_sensitive=cli_args.case_sensitive,
                    ),
                    "count_from_them": get_phrase_counts(
                        filtered_messages.filter(~pl.col("is_from_me")),
                        cli_args.phrases,
                        use_regex=cli_args.use_regex,
                        case_sensitive=cli_args.case_sensitive,
                    ),
                }
            )
        ),
        format=cli_args.format,
        output=cli_args.output,
        prettify_index=False,
    )


if __name__ == "__main__":
    main()
