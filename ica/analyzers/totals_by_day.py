#!/usr/bin/env python3
import ica

# The format to use for all date strings
DATE_FORMAT = "%Y-%m-%d"


def main() -> None:
    """
    Generates a comprehensive breakdown of message totals for every day you and
    the other participants have been messaging in the conversation
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
        (
            dfs.messages.resample("D", on="datetime")["is_from_me"]
            .agg(["count", "sum"])
            .assign(sent_by_them=lambda df: df["count"] - df["sum"])
            .loc[lambda df: df["count"] > 0]
            .rename(
                columns={
                    "count": "#_sent",
                    "sum": "#_sent_by_me",
                    "sent_by_them": "#_sent_by_them",
                }
            )
            .rename_axis(index="date")
        ),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
