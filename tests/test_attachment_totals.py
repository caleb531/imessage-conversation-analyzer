#!/usr/bin/env python3
"""test the attachment_totals built-in analyzer"""

from unittest.mock import MagicMock, patch

import ica.analyzers.attachment_totals as attachment_totals


def get_total(data: list[dict], type_name: str) -> int:
    for item in data:
        if item["type"] == type_name:
            return item["total"]
    return -1


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Jane Fernbrook"])
def test_gif_count(output_results: MagicMock) -> None:
    """Should count the number of GIFs for a conversation."""
    attachment_totals.main()
    data = output_results.call_args[0][0]
    assert get_total(data, "gifs") == 1


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_youtube_video_count(output_results: MagicMock) -> None:
    """Should count the number of YouTube videos for a conversation."""
    attachment_totals.main()
    data = output_results.call_args[0][0]
    assert get_total(data, "youtube_videos") == 4


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_apple_music_count(output_results: MagicMock) -> None:
    """Should count the number of Apple Music links for a conversation."""
    attachment_totals.main()
    data = output_results.call_args[0][0]
    assert get_total(data, "apple_music") == 1


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_spotify_count(output_results: MagicMock) -> None:
    """Should count the number of Spotify links for a conversation."""
    attachment_totals.main()
    data = output_results.call_args[0][0]
    assert get_total(data, "spotify") == 1
