#!/usr/bin/env python3

import ica


def main() -> None:
    """
    Generates a full, unedited transcript of every message, including reactions,
    between you and the other participants (attachment files not included)
    """
    cli_args = ica.get_cli_parser().parse_args(namespace=ica.TypedCLIArguments())
    dfs = ica.get_dataframes(
        contacts=cli_args.contacts,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )
    ica.output_results(
        dfs.messages.assign(
            timestamp=lambda df: df["datetime"],
            is_from_me=lambda df: df["is_from_me"].map({True: "Yes", False: "No"}),
            is_reaction=lambda df: df["is_reaction"].map({True: "Yes", False: "No"}),
            # U+FFFC is the object replacement character, which appears as the
            # textual message for every attachment
            message=lambda df: df["text"].replace(
                r"\ufffc", "(attachment)", regex=True
            ),
        )
        # Output only the following columns and in this particular order
        .loc[:, ["timestamp", "is_from_me", "is_reaction", "message"]],
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
