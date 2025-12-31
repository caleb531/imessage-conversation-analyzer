#!/usr/bin/env python3


import pandas as pd

import ica


# Count the number of occurrences of the given regular expression pattern within
# the provided Series
def count_occurrences(series: pd.Series, pattern: str) -> int:
    return series.str.count(pattern).sum()


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
        from_person=cli_args.from_person,
    )

    is_reaction = dfs.messages["is_reaction"]
    totals_map = {
        "gifs": dfs.attachments["mime_type"].eq("image/gif").sum(),
        "youtube_videos": count_occurrences(
            dfs.messages[is_reaction.eq(False)]["text"],
            r"(https?://(?:www\.)(?:youtube\.com|youtu\.be)/(?:.*?)(?:\s|$))",
        ),
        "apple_music": count_occurrences(
            dfs.messages[is_reaction.eq(False)]["text"],
            r"(https?://(?:music\.apple\.com)/(?:.*?)(?:\s|$))",
        ),
        "spotify": count_occurrences(
            dfs.messages[is_reaction.eq(False)]["text"],
            r"(https?://(?:open\.spotify\.com)/(?:.*?)(?:\s|$))",
        ),
        "audio_messages": (dfs.attachments["filename"].str.endswith(".caf").sum()),
        "audio_files": (dfs.attachments["filename"].str.endswith(".m4a").sum()),
        "recorded_videos": (dfs.attachments["mime_type"].eq("video/quicktime").sum()),
    }
    ica.output_results(
        pd.DataFrame({"type": totals_map.keys(), "total": totals_map.values()})
        .set_index("type")
        .sort_values(by="total", ascending=False),
        format=cli_args.format,
        output=cli_args.output,
        prettified_label_overrides={
            "youtube_videos": "YouTube Videos",
            "gifs": "GIFs",
        },
    )


if __name__ == "__main__":
    main()
