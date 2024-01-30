#!/usr/bin/env python3
"""test the attachment_totals built-in analyzer"""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from nose2.tools.decorators import with_setup, with_teardown

import ica.analyzers.attachment_totals as attachment_totals
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Jane Fernbrook"])
def test_gif_count(output_results: MagicMock) -> None:
    """should count the number of GIFs for a conversation"""
    attachment_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    case.assertEqual(df.loc["gifs"]["total"], 1)


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_youtube_video_count(output_results: MagicMock) -> None:
    """should count the number of YouTube videos for a conversation"""
    attachment_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    case.assertEqual(df.loc["youtube_videos"]["total"], 2)


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_apple_music_count(output_results: MagicMock) -> None:
    """should count the number of Apple Music links for a conversation"""
    attachment_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    case.assertEqual(df.loc["apple_music"]["total"], 1)


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [attachment_totals.__file__, "-c", "Thomas Riverstone"])
def test_spotify_count(output_results: MagicMock) -> None:
    """should count the number of Spotify links for a conversation"""
    attachment_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    case.assertEqual(df.loc["spotify"]["total"], 1)
