#!/usr/bin/env python3
"""test the attachment_totals built-in analyzer"""

from unittest.mock import MagicMock, patch

import pandas as pd

import ica.analyzers.attachment_totals as attachment_totals
from ica.core import DataFrameNamespace


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Jane Fernbrook"])
def test_gif_count(output_results: MagicMock) -> None:
    """Should count the number of GIFs for a conversation."""
    attachment_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    assert df.loc["gifs"]["total"] == 1


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_youtube_video_count(output_results: MagicMock) -> None:
    """Should count the number of YouTube videos for a conversation."""
    attachment_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    assert df.loc["youtube_videos"]["total"] == 4


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_apple_music_count(output_results: MagicMock) -> None:
    """Should count the number of Apple Music links for a conversation."""
    attachment_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    assert df.loc["apple_music"]["total"] == 1


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_spotify_count(output_results: MagicMock) -> None:
    """Should count the number of Spotify links for a conversation."""
    attachment_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    assert df.loc["spotify"]["total"] == 1


@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_per_sender_totals_columns(output_results: MagicMock) -> None:
    """Should include per-sender totals for each attachment metric."""
    attachment_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]

    sender_columns = [col for col in df.columns if col.startswith("total_from_")]

    assert "total_from_Me" in sender_columns
    assert len(sender_columns) >= 2
    assert (df[sender_columns].sum(axis=1) == df["total"]).all()


@patch("ica.output_results")
@patch("ica.get_dataframes")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_null_attachment_filenames(
    mock_get_dataframes: MagicMock,
    output_results: MagicMock,
) -> None:
    """Should gracefully handle null attachment filenames when counting audio."""
    mock_get_dataframes.return_value = DataFrameNamespace(
        messages=pd.DataFrame(
            {
                "text": ["hello"],
                "is_reaction": [False],
                "sender_display_name": ["Thomas"],
                "is_from_me": [False],
            }
        ),
        attachments=pd.DataFrame(
            {
                "mime_type": ["image/gif"],
                "filename": [None],
                "sender_handle": ["+15555555555"],
                "is_from_me": [False],
            }
        ),
        handles=pd.DataFrame(
            {
                "identifier": ["+15555555555"],
                "display_name": ["Thomas"],
            }
        ),
    )

    attachment_totals.main()

    df: pd.DataFrame = output_results.call_args[0][0]
    assert df.loc["audio_messages"]["total"] == 0
    assert df.loc["audio_files"]["total"] == 0
