#!/usr/bin/env python3
"""test the ability to filter analyzer results by date and person"""

from unittest.mock import MagicMock, patch

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
    rel = output_results.call_args[0][0]
    data = [dict(zip(rel.columns, row)) for row in rel.fetchall()]
    dates = [row["date"] for row in data]
    expected_dates = [
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
        "2024-01-17",
        "2024-01-19",
    ]
    assert dates == expected_dates


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
    rel = output_results.call_args[0][0]
    data = [dict(zip(rel.columns, row)) for row in rel.fetchall()]
    dates = [row["date"] for row in data]
    expected_dates = [
        "2024-01-07",
        "2024-01-08",
        "2024-01-09",
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
    ]
    assert dates == expected_dates


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
    rel = output_results.call_args[0][0]
    data = [dict(zip(rel.columns, row)) for row in rel.fetchall()]
    dates = [row["date"] for row in data]
    expected_dates = [
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
    ]
    assert dates == expected_dates


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
    data = output_results.call_args[0][0]
    result = {row["type"]: row["total"] for row in data}
    assert result["youtube_videos"] == 1
    assert result["apple_music"] == 1
    assert result["spotify"] == 1


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
    data = output_results.call_args[0][0]
    result = {row["type"]: row["total"] for row in data}
    assert result["youtube_videos"] == 3
    assert result.get("apple_music", 0) == 0
    assert result.get("spotify", 0) == 0


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
    data = output_results.call_args[0][0]
    result = {row["type"]: row["total"] for row in data}
    assert result["youtube_videos"] == 4
    assert result["apple_music"] == 1
    assert result["spotify"] == 1
