#!/usr/bin/env python3
"""test the ability to filter analyzer results by date and person"""

from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import polars as pl
import pytest

import ica
import ica.analyzers.attachment_totals as attachment_totals
import ica.analyzers.totals_by_day as totals_by_day


@patch("ica.output_results")
@patch(
    "sys.argv",
    [
        totals_by_day.__file__,
        "-c",
        "Jane Fernbrook",
        "-t",
        "UTC",
        "--from-date",
        "2024-01-11",
    ],
)
def test_from_date(output_results: MagicMock) -> None:
    """
    Should filter the results to those sent at or after the specified date.
    """
    totals_by_day.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    expected_dates = [
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
        "2024-01-17",
        "2024-01-19",
    ]
    # Polars datetimes are python datetime objects when converted to list
    assert df["date"].to_list() == [
        datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=ZoneInfo("UTC"))
        for date in expected_dates
    ]


@patch("ica.output_results")
@patch(
    "sys.argv",
    [
        totals_by_day.__file__,
        "-c",
        "Jane Fernbrook",
        "-t",
        "UTC",
        "--to-date",
        "2024-01-17",
    ],
)
def test_to_date(output_results: MagicMock) -> None:
    """
    Should filter the results to those sent before the specified date.
    """
    totals_by_day.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    expected_dates = [
        "2024-01-07",
        "2024-01-08",
        "2024-01-09",
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
    ]
    assert df["date"].to_list() == [
        datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=ZoneInfo("UTC"))
        for date in expected_dates
    ]


@patch("ica.output_results")
@patch(
    "sys.argv",
    [
        totals_by_day.__file__,
        "-c",
        "Jane Fernbrook",
        "-t",
        "UTC",
        "--from-date",
        "2024-01-11",
        "--to-date",
        "2024-01-17",
    ],
)
def test_date_range(output_results: MagicMock) -> None:
    """
    Should filter the results to those sent between the specified dates.
    """
    totals_by_day.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    expected_dates = [
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
    ]
    assert df["date"].to_list() == [
        datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=ZoneInfo("UTC"))
        for date in expected_dates
    ]


@patch("ica.output_results")
@patch(
    "sys.argv",
    [
        totals_by_day.__file__,
        "-c",
        "Jane Fernbrook",
        "-t",
        "UTC",
        "--from-date",
        "2024-01-17",
        "--to-date",
        "2024-01-11",
    ],
)
def test_invalid_date_range(output_results: MagicMock) -> None:
    """
    Should filter the results to those sent between the specified dates.
    """
    with pytest.raises(ica.DateRangeInvalidError):
        totals_by_day.main()


@patch("ica.output_results")
@patch(
    "sys.argv",
    [
        attachment_totals.__file__,
        "-c",
        "Thomas Riverstone",
        "-t",
        "UTC",
        "--from-person",
        "me",
    ],
)
def test_from_person_me(output_results: MagicMock) -> None:
    """
    Should filter the results to those sent by the person running the
    command.
    """
    attachment_totals.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    assert df.filter(pl.col("metric") == "youtube_videos")["total"].item() == 1
    assert df.filter(pl.col("metric") == "apple_music")["total"].item() == 1
    assert df.filter(pl.col("metric") == "spotify")["total"].item() == 1


@patch("ica.output_results")
@patch(
    "sys.argv",
    [
        attachment_totals.__file__,
        "-c",
        "Thomas Riverstone",
        "-t",
        "UTC",
        "--from-person",
        "them",
    ],
)
def test_from_person_them(output_results: MagicMock) -> None:
    """
    Should filter the results to those sent by the other participant.
    """
    attachment_totals.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    assert df.filter(pl.col("metric") == "youtube_videos")["total"].item() == 3
    assert df.filter(pl.col("metric") == "apple_music")["total"].item() == 0
    assert df.filter(pl.col("metric") == "spotify")["total"].item() == 0


@patch("ica.output_results")
@patch(
    "sys.argv",
    [
        attachment_totals.__file__,
        "-c",
        "Thomas Riverstone",
        "-t",
        "UTC",
        "--from-person",
        "both",
    ],
)
def test_from_person_both(output_results: MagicMock) -> None:
    """
    Should filter the results to those sent by either participant (i.e. no
    filtering is applied).
    """
    attachment_totals.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    assert df.filter(pl.col("metric") == "youtube_videos")["total"].item() == 4
    assert df.filter(pl.col("metric") == "apple_music")["total"].item() == 1
    assert df.filter(pl.col("metric") == "spotify")["total"].item() == 1
