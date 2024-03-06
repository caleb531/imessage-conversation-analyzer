#!/usr/bin/env python3


import pandas as pd

import ica


def main() -> None:
    """
    Generate count data by attachment type, including number of Spotify links
    shared, YouTube videos, Apple Music, etc.
    """
    cli_args = ica.get_cli_args()
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name, timezone=cli_args.timezone
    )
    totals_map = {
        "gifs": dfs.attachments["mime_type"].eq("image/gif").sum(),
        "youtube_videos": (
            dfs.messages["text"]
            .str.extract(
                r"(https?://(?:www\.)(?:youtube\.com|youtu\.be)/(?:.*?)(?:\s|$))"
            )
            .drop_duplicates()
            .count()
            .item()
        ),
        "apple_music": (
            dfs.messages["text"]
            .str.extract(r"(https?://(?:music\.apple\.com)/(?:.*?)(?:\s|$))")
            .drop_duplicates()
            .count()
            .item()
        ),
        "spotify": (
            dfs.messages["text"]
            .str.extract(r"(https?://(?:open\.spotify\.com)/(?:.*?)(?:\s|$))")
            .drop_duplicates()
            .count()
            .item()
        ),
        "audio_messages": (dfs.attachments["filename"].str.endswith(".caf").sum()),
        "recorded_videos": (dfs.attachments["mime_type"].eq("video/quicktime").sum()),
    }
    ica.output_results(
        pd.DataFrame({"type": totals_map.keys(), "total": totals_map.values()})
        .set_index("type")
        .sort_values(by="total", ascending=False),
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
