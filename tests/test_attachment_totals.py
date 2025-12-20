#!/usr/bin/env python3
"""test the attachment_totals built-in analyzer"""

from unittest.mock import MagicMock, patch

import polars as pl

import ica.analyzers.attachment_totals as attachment_totals


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Jane Fernbrook"])
def test_gif_count(output_results: MagicMock) -> None:
    """Should count the number of GIFs for a conversation."""
    attachment_totals.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    assert df.filter(pl.col("metric") == "gifs")["total"].item() == 1


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_youtube_video_count(output_results: MagicMock) -> None:
    """Should count the number of YouTube videos for a conversation."""
    attachment_totals.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    assert df.filter(pl.col("metric") == "youtube_videos")["total"].item() == 4


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_apple_music_count(output_results: MagicMock) -> None:
    """Should count the number of Apple Music links for a conversation."""
    attachment_totals.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    assert df.filter(pl.col("metric") == "apple_music")["total"].item() == 1


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_spotify_count(output_results: MagicMock) -> None:
    """Should count the number of Spotify links for a conversation."""
    attachment_totals.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    assert df.filter(pl.col("metric") == "spotify")["total"].item() == 1
