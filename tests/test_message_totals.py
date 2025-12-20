#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

from unittest.mock import MagicMock, patch

import polars as pl
from freezegun import freeze_time

import ica.analyzers.message_totals as message_totals


@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook"])
def test_message_counts(output_results: MagicMock) -> None:
    """Should count the number of messages according to various criteria."""
    message_totals.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    assert df.filter(pl.col("metric") == "messages")["total"].item() == 9
    assert df.filter(pl.col("metric") == "messages_from_me")["total"].item() == 5
    assert df.filter(pl.col("metric") == "messages_from_them")["total"].item() == 4


@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook"])
def test_reaction_counts(output_results: MagicMock) -> None:
    """Should count the number of reactions according to various
    criteria."""
    message_totals.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    assert df.filter(pl.col("metric") == "reactions")["total"].item() == 2
    assert df.filter(pl.col("metric") == "reactions_from_me")["total"].item() == 0
    assert df.filter(pl.col("metric") == "reactions_from_them")["total"].item() == 2


@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook"])
@freeze_time("2024-01-26 9:00:00")
def test_day_counts(output_results: MagicMock) -> None:
    """Should count the number of days according to various criteria."""
    message_totals.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    assert df.filter(pl.col("metric") == "days_messaged")["total"].item() == 8
    assert df.filter(pl.col("metric") == "days_missed")["total"].item() == 12
    assert df.filter(pl.col("metric") == "days_with_no_reply")["total"].item() == 6
