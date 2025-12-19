#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

from unittest.mock import MagicMock, patch

from freezegun import freeze_time

import ica.analyzers.message_totals as message_totals


def get_metric(data: list[dict], metric: str) -> int:
    for item in data:
        if item["metric"] == metric:
            return item["total"]
    return -1


@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook"])
def test_message_counts(output_results: MagicMock) -> None:
    """Should count the number of messages according to various criteria."""
    message_totals.main()
    data = output_results.call_args[0][0]
    assert get_metric(data, "messages") == 9
    assert get_metric(data, "messages_from_me") == 5
    assert get_metric(data, "messages_from_them") == 4


@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook"])
def test_reaction_counts(output_results: MagicMock) -> None:
    """Should count the number of reactions according to various
    criteria."""
    message_totals.main()
    data = output_results.call_args[0][0]
    assert get_metric(data, "reactions") == 2
    assert get_metric(data, "reactions_from_me") == 0
    assert get_metric(data, "reactions_from_them") == 2


@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook", "-t", "UTC"])
@freeze_time("2024-01-26 9:00:00")
def test_day_counts(output_results: MagicMock) -> None:
    """Should count the number of days according to various criteria."""
    message_totals.main()
    data = output_results.call_args[0][0]
    assert get_metric(data, "days_messaged") == 8
    assert get_metric(data, "days_missed") == 12
    assert get_metric(data, "days_with_no_reply") == 6
