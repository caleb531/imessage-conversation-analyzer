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
        from_people=cli_args.from_people,
    )

    daily_counts = dfs.messages.assign(
        date=lambda df: df["datetime"].dt.floor("D")
    ).pivot_table(
        index="date",
        columns="sender_display_name",
        values="text",
        aggfunc="count",
        fill_value=0,
    )

    # Ensure all participants (and "Me") are represented as columns
    all_participants: list[str] = sorted(dfs.handles["display_name"].unique())
    expected_cols = ["Me"] + all_participants
    daily_counts = daily_counts.reindex(columns=expected_cols, fill_value=0)

    # Rename columns
    daily_counts = daily_counts.rename(
        columns=lambda col: "total_sent_by_me"
        if col == "Me"
        else f"total_sent_by_{col}"
    )

    # Calculate total sent
    daily_counts["total_sent"] = daily_counts.sum(axis=1)

    # Filter days with > 0 messages
    daily_counts = daily_counts[daily_counts["total_sent"] > 0]

    # Reorder columns
    cols = ["total_sent", "total_sent_by_me"] + [
        f"total_sent_by_{name}" for name in all_participants
    ]
    daily_counts = daily_counts[cols]

    ica.output_results(
        daily_counts,
        format=cli_args.format,
        output=cli_args.output,
        prettified_label_overrides={
            f"total_sent_by_{display_name}": f"Total Sent By {display_name}"
            for display_name in all_participants
        },
    )


if __name__ == "__main__":
    main()
