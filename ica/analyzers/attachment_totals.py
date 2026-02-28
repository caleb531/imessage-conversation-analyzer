#!/usr/bin/env python3

from typing import Union

import pandas as pd

import ica


def reindex_sender_counts(
    counts: pd.Series,
    expected_senders: list[str],
) -> pd.Series:
    return counts.reindex(expected_senders, fill_value=0).astype(int)


def main() -> None:
    """
    Generate count data by attachment type, including number of Spotify links
    shared, YouTube videos, Apple Music, etc.
    """
    cli_args = ica.get_cli_parser().parse_args(namespace=ica.TypedCLIArguments())
    dfs = ica.get_dataframes(
        contacts=cli_args.contacts,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_people=cli_args.from_people,
    )

    all_participants = sorted(dfs.handles["display_name"].unique())
    expected_senders = ["Me", *all_participants]

    handles_by_identifier = dfs.handles.set_index("identifier")["display_name"]

    messages = (
        dfs.messages.loc[dfs.messages["is_reaction"].eq(False)]
        .assign(sender_column=lambda data: data["sender_display_name"])
        .assign(
            sender_column=lambda data: data["sender_column"].where(
                data["is_from_me"].eq(False),
                "Me",
            )
        )
    )

    attachments = dfs.attachments.assign(
        sender_column=lambda data: data["sender_handle"]
        .map(handles_by_identifier)
        .where(
            data["is_from_me"].eq(False),
            "Me",
        )
    )

    def build_message_metric_row(
        metric_type: str, pattern: str
    ) -> dict[str, Union[int, str]]:
        per_sender = reindex_sender_counts(
            messages.assign(match_count=lambda data: data["text"].str.count(pattern))
            .groupby("sender_column")["match_count"]
            .sum(),
            expected_senders,
        )
        return {
            "type": metric_type,
            "total": int(per_sender.sum()),
            **per_sender.rename(lambda sender: f"total_from_{sender}").to_dict(),
        }

    def build_attachment_metric_row(
        metric_type: str,
        mask: pd.Series,
    ) -> dict[str, Union[int, str]]:
        per_sender = reindex_sender_counts(
            attachments.loc[mask, "sender_column"].value_counts(),
            expected_senders,
        )
        return {
            "type": metric_type,
            "total": int(per_sender.sum()),
            **per_sender.rename(lambda sender: f"total_from_{sender}").to_dict(),
        }

    rows = [
        build_attachment_metric_row("gifs", attachments["mime_type"].eq("image/gif")),
        build_message_metric_row(
            "youtube_videos",
            r"(https?://(?:www\.)(?:youtube\.com|youtu\.be)/(?:.*?)(?:\s|$))",
        ),
        build_message_metric_row(
            "apple_music",
            r"(https?://(?:music\.apple\.com)/(?:.*?)(?:\s|$))",
        ),
        build_message_metric_row(
            "spotify",
            r"(https?://(?:open\.spotify\.com)/(?:.*?)(?:\s|$))",
        ),
        build_attachment_metric_row(
            "audio_messages", attachments["filename"].str.endswith(".caf", na=False)
        ),
        build_attachment_metric_row(
            "audio_files", attachments["filename"].str.endswith(".m4a", na=False)
        ),
        build_attachment_metric_row(
            "recorded_videos", attachments["mime_type"].eq("video/quicktime")
        ),
    ]

    ica.output_results(
        pd.DataFrame(rows).set_index("type").sort_values(by="total", ascending=False),
        format=cli_args.format,
        output=cli_args.output,
        prettified_label_overrides={
            "youtube_videos": "YouTube Videos",
            "gifs": "GIFs",
            **{
                f"total_from_{display_name}": f"Total From {display_name}"
                for display_name in all_participants
            },
        },
    )


if __name__ == "__main__":
    main()
