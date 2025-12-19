#!/usr/bin/env python3

import re

import ica


class CountPhrasesArgumentParser(ica.TypedCLIArguments):
    """Additional CLI arguments specific to the count_phrases analyzer"""

    phrases: list[str]
    use_regex: bool
    case_sensitive: bool


def get_phrase_counts(
    data: ica.ConversationData,
    phrases: list[str],
    use_regex: bool = False,
    case_sensitive: bool = False,
) -> list[dict]:
    results = []

    messages_filtered = data.messages.filter("is_reaction IS NULL")

    for phrase in phrases:
        pattern = phrase
        if not use_regex:
            pattern = re.escape(pattern)

        if not case_sensitive:
            pattern = f"(?i){pattern}"

        # DuckDB query
        # We need to sum the count of matches per row
        # sum(len(regexp_extract_all(text, ?)))

        pattern_sql = pattern.replace("'", "''")

        # Total
        res = messages_filtered.aggregate(
            f"sum(len(regexp_extract_all(text, '{pattern_sql}')))"
        ).fetchone()
        total = (res[0] if res else 0) or 0

        # From me
        res = (
            messages_filtered.filter("is_from_me = true")
            .aggregate(f"sum(len(regexp_extract_all(text, '{pattern_sql}')))")
            .fetchone()
        )
        from_me = (res[0] if res else 0) or 0

        # From them
        res = (
            messages_filtered.filter("is_from_me = false")
            .aggregate(f"sum(len(regexp_extract_all(text, '{pattern_sql}')))")
            .fetchone()
        )
        from_them = (res[0] if res else 0) or 0

        results.append(
            {
                "phrase": phrase,
                "count": total,
                "count_from_me": from_me,
                "count_from_them": from_them,
            }
        )

    return results


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
    data = ica.get_conversation_data(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    results = get_phrase_counts(
        data,
        cli_args.phrases,
        use_regex=cli_args.use_regex,
        case_sensitive=cli_args.case_sensitive,
    )

    ica.output_results(
        results,
        format=cli_args.format,
        output=cli_args.output,
        prettify_index=False,
    )


if __name__ == "__main__":
    main()
