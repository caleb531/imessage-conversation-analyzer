#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

from unittest.mock import MagicMock, patch

import pandas as pd
from freezegun import freeze_time

import ica.analyzers.message_totals as message_totals


class TestMessageTotals:
    """
    Test cases for the `message_totals` analyzer, which calculates totals for
    messages, reactions, and days messaged in a conversation.
    """

    @patch("ica.output_results")
    @patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook"])
    def test_message_counts(self, output_results: MagicMock) -> None:
        """Should count the number of messages according to various criteria."""
        message_totals.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        assert df.loc["messages"]["total"] == 9
        assert df.loc["messages_from_me"]["total"] == 5
        assert df.loc["messages_from_them"]["total"] == 4

    @patch("ica.output_results")
    @patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook"])
    def test_reaction_counts(self, output_results: MagicMock) -> None:
        """Should count the number of reactions according to various
        criteria."""
        message_totals.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        assert df.loc["reactions"]["total"] == 2
        assert df.loc["reactions_from_me"]["total"] == 0
        assert df.loc["reactions_from_them"]["total"] == 2

    @patch("ica.output_results")
    @patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook"])
    @freeze_time("2024-01-26 9:00:00")
    def test_day_counts(self, output_results: MagicMock) -> None:
        """Should count the number of days according to various criteria."""
        message_totals.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        assert df.loc["days_messaged"]["total"] == 8
        assert df.loc["days_missed"]["total"] == 12
        assert df.loc["days_with_no_reply"]["total"] == 6
