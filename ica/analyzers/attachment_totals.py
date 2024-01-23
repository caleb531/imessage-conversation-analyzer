#!/usr/bin/env python3


import pandas as pd

import ica


def main() -> None:
    cli_args = ica.get_cli_args()
    dfs = ica.get_dataframes(contact_name=cli_args.contact_name)
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
        "recorded_videos": (dfs.attachments["mime_type"].eq("video/quicktime").sum()),
    }
    attachment_totals = pd.DataFrame(
        {"type": totals_map.keys(), "total": totals_map.values()}
    )
    ica.output_results(
        attachment_totals.sort_values(by="total", ascending=False).reset_index(
            drop=True
        ),
        format=cli_args.format,
    )


if __name__ == "__main__":
    main()