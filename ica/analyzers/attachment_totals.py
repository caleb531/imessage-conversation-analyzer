#!/usr/bin/env python3


import polars as pl

import ica


# Count the number of occurrences of the given regular expression pattern within
# the provided Series
def count_occurrences(series: pl.Series, pattern: str) -> int:
    # Use str.count_matches for regex counting in Polars
    return series.str.count_matches(pattern).sum()


def main() -> None:
    """
    Generate count data by attachment type, including number of Spotify links
    shared, YouTube videos, Apple Music, etc.
    """
    cli_args = ica.get_cli_parser().parse_args(namespace=ica.TypedCLIArguments())
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    # Filter out reactions
    messages_no_reactions = dfs.messages.filter(~pl.col("is_reaction"))

    totals_map = {
        "gifs": dfs.attachments.filter(pl.col("mime_type") == "image/gif").height,
        "youtube_videos": count_occurrences(
            messages_no_reactions["text"],
            r"(https?://(?:www\.)(?:youtube\.com|youtu\.be)/(?:.*?)(?:\s|$))",
        ),
        "apple_music": count_occurrences(
            messages_no_reactions["text"],
            r"(https?://(?:music\.apple\.com)/(?:.*?)(?:\s|$))",
        ),
        "spotify": count_occurrences(
            messages_no_reactions["text"],
            r"(https?://(?:open\.spotify\.com)/(?:.*?)(?:\s|$))",
        ),
        "audio_messages": (
            dfs.attachments.filter(pl.col("filename").str.ends_with(".caf")).height
        ),
        "audio_files": (
            dfs.attachments.filter(pl.col("filename").str.ends_with(".m4a")).height
        ),
        "recorded_videos": (
            dfs.attachments.filter(pl.col("mime_type") == "video/quicktime").height
        ),
    }
    ica.output_results(
        pl.DataFrame(
            {"type": list(totals_map.keys()), "total": list(totals_map.values())}
        ).sort("total", descending=True),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
