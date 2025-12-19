#!/usr/bin/env python3

import ica


# Count the number of occurrences of the given regular expression pattern within
# the provided Relation
def count_occurrences(data: ica.ConversationData, pattern: str) -> int:
    # Filter out reactions first
    # We use regexp_extract_all to find all matches, then len() to count them,
    # then sum() to get total
    # Note: We need to handle the case where text is NULL (though it shouldn't
    # be after COALESCE)
    # Also, we need to be careful with regex syntax in DuckDB.
    # Python's regex might differ slightly from RE2 (DuckDB's regex engine).
    # The patterns used here seem standard.

    # Escape single quotes for SQL string interpolation
    pattern_sql = pattern.replace("'", "''")

    result = (
        data.messages.filter("is_reaction IS NULL")
        .aggregate(f"sum(len(regexp_extract_all(text, '{pattern_sql}')))")
        .fetchone()
    )

    return result[0] if result and result[0] is not None else 0


def main() -> None:
    """
    Generate count data by attachment type, including number of Spotify links
    shared, YouTube videos, Apple Music, etc.
    """
    cli_args = ica.get_cli_parser().parse_args(namespace=ica.TypedCLIArguments())
    data = ica.get_conversation_data(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    # Attachments counts
    # We can use SQL on the attachments relation
    res = (
        data.attachments.filter("mime_type = 'image/gif'")
        .aggregate("count(*)")
        .fetchone()
    )
    gifs = res[0] if res else 0

    res = (
        data.attachments.filter("filename LIKE '%.caf'")
        .aggregate("count(*)")
        .fetchone()
    )
    audio_messages = res[0] if res else 0

    res = (
        data.attachments.filter("filename LIKE '%.m4a'")
        .aggregate("count(*)")
        .fetchone()
    )
    audio_files = res[0] if res else 0

    res = (
        data.attachments.filter("mime_type = 'video/quicktime'")
        .aggregate("count(*)")
        .fetchone()
    )
    recorded_videos = res[0] if res else 0

    totals_map = {
        "gifs": gifs,
        "youtube_videos": count_occurrences(
            data,
            r"(https?://(?:www\.)(?:youtube\.com|youtu\.be)/(?:.*?)(?:\s|$))",
        ),
        "apple_music": count_occurrences(
            data,
            r"(https?://(?:music\.apple\.com)/(?:.*?)(?:\s|$))",
        ),
        "spotify": count_occurrences(
            data,
            r"(https?://(?:open\.spotify\.com)/(?:.*?)(?:\s|$))",
        ),
        "audio_messages": audio_messages,
        "audio_files": audio_files,
        "recorded_videos": recorded_videos,
    }

    # Sort by total descending
    sorted_totals = sorted(totals_map.items(), key=lambda x: x[1], reverse=True)

    ica.output_results(
        [{"type": k, "total": v} for k, v in sorted_totals],
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
