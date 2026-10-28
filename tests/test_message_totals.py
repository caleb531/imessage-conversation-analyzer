#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

from typing import Optional
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from freezegun import freeze_time

import ica.analyzers.message_totals as message_totals
from ica import DataFrameNamespace


@pytest.mark.parametrize(
    ("dates", "expected"),
    [
        ([], None),
        ([None], None),
        (["2024-01-08 23:30:00", "2024-01-09 10:00:00"], "2024-01-08"),
    ],
)
def test_first_message_date(
    dates: list[Optional[str]], expected: Optional[str]
) -> None:
    """Return the earliest local date, or None if there are no valid dates."""
    # The messages include a timezone to check that we retain their local date.
    dfs = DataFrameNamespace(
        messages=pd.DataFrame(
            {"datetime": pd.Series(dates, dtype="datetime64[ns, America/Los_Angeles]")}
        ),
        attachments=pd.DataFrame(),
        handles=pd.DataFrame(),
    )
    # The first date should have no time or timezone information.
    result = message_totals.get_first_message_date(dfs)
    if expected is None:
        assert result is None
    else:
        assert result == pd.Timestamp(expected)


@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook", "-t", "UTC"])
def test_message_counts(output_results: MagicMock) -> None:
    """Should count the number of messages according to various criteria."""
    message_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    assert df.loc["messages"]["total"] == 9
    assert df.loc["messages_from_me"]["total"] == 5
    assert df.loc["messages_from_jane"]["total"] == 4


@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook", "-t", "UTC"])
def test_reaction_counts(output_results: MagicMock) -> None:
    """Should count the number of reactions according to various
    criteria."""
    message_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    assert df.loc["reactions"]["total"] == 2
    assert df.loc["reactions_from_me"]["total"] == 0
    assert df.loc["reactions_from_jane"]["total"] == 2


@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook", "-t", "UTC"])
@freeze_time("2024-01-26 9:00:00")
def test_day_counts(output_results: MagicMock) -> None:
    """Should count the number of days according to various criteria."""
    message_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    assert df.loc["days_messaged"]["total"] == 7
    assert df.loc["days_missed"]["total"] == 12
    assert df.loc["days_with_no_reply"]["total"] == 4


@patch("ica.output_results")
@patch(
    "sys.argv",
    [
        message_totals.__file__,
        "-c",
        "Jane Fernbrook",
        "-t",
        "UTC",
        "--from-date",
        "2030-01-01",
        "--to-date",
        "2030-01-02",
    ],
)
def test_no_messages(output_results: MagicMock) -> None:
    """Should handle cases where no messages are found."""
    message_totals.main()

    df: pd.DataFrame = output_results.call_args[0][0]
    assert df.loc["messages"]["total"] == 0
    assert df.loc["days_messaged"]["total"] == 0
    assert df.loc["days_missed"]["total"] == 0


@patch("ica.output_results")
@patch(
    "sys.argv",
    [
        message_totals.__file__,
        "-c",
        "Jane Fernbrook",
        "-t",
        "UTC",
        "--to-date",
        "2024-01-10",
    ],
)
@freeze_time("2024-02-01")
def test_date_upper_bound(output_results: MagicMock) -> None:
    """
    Should constrain the Days Messaged and Days Missed calculation to the
    provided end date, or today's date (whichever is earlier)
    """
    message_totals.main()
    df: pd.DataFrame = output_results.call_args[0][0]

    # First message is 2024-01-08
    # to_date is 2024-01-10 (midnight).
    # Included days: Jan 8, 9, 10. (3 days).
    # Messages exist on Jan 8, 9. (2 days).
    # Jan 10 has no messages (because to_date is exclusive for messages after midnight).

    assert df.loc["days_messaged"]["total"] == 2
    assert df.loc["days_missed"]["total"] == 1

    # Verify that it's not using "today" (Feb 1)
    # If it used Feb 1: Total days = 26. Days missed = 23.
    assert df.loc["days_missed"]["total"] != 23
