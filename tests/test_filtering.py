#!/usr/bin/env python3
"""test the ability to filter analyzer results by date and person"""

import contextlib
import importlib
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest

import ica
from tests.utils import MockSuccess


def test_from_date() -> None:
    """
    Should filter the results to those sent at or after the specified date.
    """
    dfs = ica.get_dataframes(
        contacts=["Jane Fernbrook"],
        timezone="UTC",
        from_date="2024-01-11",
    )
    expected_dates = [
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
        "2024-01-17",
        "2024-01-19",
    ]
    unique_dates = sorted(dfs.messages["datetime"].dt.floor("D").unique())
    assert unique_dates == [pd.Timestamp(date, tz="UTC") for date in expected_dates]


def test_to_date() -> None:
    """
    Should filter the results to those sent before the specified date.
    """
    dfs = ica.get_dataframes(
        contacts=["Jane Fernbrook"],
        timezone="UTC",
        to_date="2024-01-17",
    )
    expected_dates = [
        # This date was previously 2024-01-07, but we changed the mock data
        # timestamp
        "2024-01-08",
        "2024-01-09",
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
    ]
    unique_dates = sorted(dfs.messages["datetime"].dt.floor("D").unique())
    assert unique_dates == [pd.Timestamp(date, tz="UTC") for date in expected_dates]


def test_date_range() -> None:
    """
    Should filter the results to those sent between the specified dates.
    """
    dfs = ica.get_dataframes(
        contacts=["Jane Fernbrook"],
        timezone="UTC",
        from_date="2024-01-11",
        to_date="2024-01-17",
    )
    expected_dates = [
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
    ]
    unique_dates = sorted(dfs.messages["datetime"].dt.floor("D").unique())
    assert unique_dates == [pd.Timestamp(date, tz="UTC") for date in expected_dates]


def test_invalid_date_range() -> None:
    """
    Should filter the results to those sent between the specified dates.
    """
    with pytest.raises(ica.DateRangeInvalidError):
        ica.get_dataframes(
            contacts=["Jane Fernbrook"],
            timezone="UTC",
            from_date="2024-01-17",
            to_date="2024-01-11",
        )


def test_from_person_me() -> None:
    """
    Should filter the results to those sent by the person running the
    command.
    """
    dfs = ica.get_dataframes(
        contacts=["Thomas Riverstone"],
        from_people=["me"],
    )
    assert len(dfs.messages) == 12
    assert dfs.messages["sender_display_name"].unique().tolist() == ["Me"]

    assert dfs.messages["is_from_me"].all(), (
        "Found messages with is_from_me=False in the filtered dataframe"
    )


def test_from_person_name() -> None:
    """
    Should filter the results to those sent by the specified contact name.
    """
    dfs = ica.get_dataframes(
        contacts=["Thomas Riverstone"],
        from_people=["Thomas"],
    )
    assert len(dfs.messages) == 11
    assert dfs.messages["sender_display_name"].unique().tolist() == ["Thomas"]

    assert not dfs.messages["is_from_me"].any(), (
        "Found messages with is_from_me=True in the filtered dataframe"
    )


def test_from_person_fullname() -> None:
    """
    Should filter the results to those sent by the specified contact full name.
    """
    dfs = ica.get_dataframes(
        contacts=["Thomas Riverstone"],
        from_people=["Thomas Riverstone"],
    )
    assert len(dfs.messages) == 11
    assert dfs.messages["sender_display_name"].unique().tolist() == ["Thomas"]

    assert not dfs.messages["is_from_me"].any(), (
        "Found messages with is_from_me=True in the filtered dataframe"
    )


def test_from_person_email() -> None:
    """
    Should filter the results to those sent by the specified contact identifier.
    """
    dfs = ica.get_dataframes(
        contacts=["Thomas Riverstone"],
        from_people=["thomas.riverstone@example.com"],
    )
    assert len(dfs.messages) == 11
    assert dfs.messages["sender_display_name"].unique().tolist() == ["Thomas"]
    assert not dfs.messages["is_from_me"].any(), (
        "Found messages with is_from_me=True in the filtered dataframe"
    )


def test_from_person_all() -> None:
    """
    Should filter the results to those sent by either participant (i.e. no
    filtering is applied).
    """
    dfs = ica.get_dataframes(
        contacts=["Thomas Riverstone"],
        from_people=["all"],
    )
    assert len(dfs.messages) == 23

    senders = dfs.messages["sender_display_name"].unique().tolist()
    assert "Thomas" in senders
    assert "Me" in senders

    assert dfs.messages["is_from_me"].any(), (
        "Expected messages from me to be included with --from-person all"
    )


def test_from_person_them() -> None:
    """
    Should filter the results to those sent by anyone except the person running
    the command.
    """
    dfs = ica.get_dataframes(
        contacts=["Thomas Riverstone"],
        from_people=["them"],
    )
    assert len(dfs.messages) == 11

    assert dfs.messages["sender_display_name"].unique().tolist() == ["Thomas"]

    assert not dfs.messages["is_from_me"].any(), (
        "Found messages with is_from_me=True in the filtered dataframe"
    )


def test_from_person_not_found() -> None:
    """
    Should raise ContactNotFoundError for invalid name.
    """
    with pytest.raises(ica.ContactNotFoundError):
        ica.get_dataframes(contacts=["Thomas Riverstone"], from_people=["Bad Name"])


@pytest.mark.parametrize(
    ("analyzer_name", "required_args"),
    [
        ("message_totals", []),
        ("attachment_totals", []),
        ("most_frequent_emojis", []),
        ("totals_by_day", []),
        ("transcript", []),
        ("count_phrases", ["foo"]),
        ("from_sql", ["SELECT * FROM foo"]),
    ],
)
@pytest.mark.parametrize(
    ("filter_cli_args", "expected_kwargs"),
    [
        (
            [],
            {"from_date": None, "to_date": None, "from_people": None},
        ),
        (
            ["--from-date", "2024-01-01"],
            {"from_date": "2024-01-01", "to_date": None, "from_people": None},
        ),
        (
            ["--to-date", "2024-01-31"],
            {"from_date": None, "to_date": "2024-01-31", "from_people": None},
        ),
        (
            ["--from-date", "2024-01-01", "--to-date", "2024-01-31"],
            {"from_date": "2024-01-01", "to_date": "2024-01-31", "from_people": None},
        ),
        (
            ["--from-person", "Me"],
            {"from_date": None, "to_date": None, "from_people": ["Me"]},
        ),
        (
            ["--from-person", "Me", "--from-person", "You"],
            {"from_date": None, "to_date": None, "from_people": ["Me", "You"]},
        ),
    ],
)
@patch("ica.get_dataframes")
def test_filter_passing_in_analyzers(
    mock_get_dataframes: Any,
    filter_cli_args: list[str],
    expected_kwargs: dict[str, Any],
    analyzer_name: str,
    required_args: list[str],
) -> None:
    """
    Should ensure that the filtering arguments passed to the CLI are correctly
    parameterized into the ica.get_dataframes() function.
    """
    mock_get_dataframes.side_effect = MockSuccess

    # We must always pass a contact to satisfy the rigorous CLI parser requirements
    base_args = ["ica", "-c", "Test User"]

    with patch("sys.argv", base_args + filter_cli_args + required_args):
        # Dynamically import and run the analyzer "script"
        with contextlib.suppress(MockSuccess):
            importlib.import_module(f"ica.analyzers.{analyzer_name}").main()

    mock_get_dataframes.assert_called_once_with(
        contacts=["Test User"],
        timezone=None,
        **expected_kwargs,
    )


def test_to_date_exclusive() -> None:
    """
    Test that to_date filtering excludes messages exactly at the boundary. This
    corresponds to the < behavior (half-open interval).
    """
    # The message with ROWID "ef073cec-fcd5-4fdb-b400-c2f54a7cb974" has timestamp
    # 726442407346190720, which is exactly 2024-01-08 21:33:27.346190720 UTC
    target_date = "2024-01-08 21:33:27.346190720"
    dfs = ica.get_dataframes(
        contacts=["Jane Fernbrook"], to_date=target_date, timezone="UTC"
    )

    # Ensure we actually got some data (messages exists before the boundary)
    assert len(dfs.messages) > 0, "Should return messages before the boundary"

    # Filter to find that specific message
    boundary_msg = dfs.messages[
        dfs.messages["ROWID"] == "ef073cec-fcd5-4fdb-b400-c2f54a7cb974"
    ]
    assert len(boundary_msg) == 0, (
        "Message at exactly to_date boundary should be excluded (< logic)"
    )
