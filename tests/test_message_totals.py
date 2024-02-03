#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

from unittest.mock import MagicMock, patch

import pandas as pd
from freezegun import freeze_time

import ica.analyzers.message_totals as message_totals
from tests import ICATestCase


class TestMessageTotals(ICATestCase):

    @patch("ica.output_results")
    @patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook"])
    def test_message_counts(self, output_results: MagicMock) -> None:
        """should count the number of messages according to various criteria"""
        message_totals.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        self.assertEqual(df.loc["messages"]["total"], 9)
        self.assertEqual(df.loc["messages_from_me"]["total"], 5)
        self.assertEqual(df.loc["messages_from_them"]["total"], 4)

    @patch("ica.output_results")
    @patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook"])
    def test_reaction_counts(self, output_results: MagicMock) -> None:
        """should count the number of reactions according to various criteria"""
        message_totals.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        self.assertEqual(df.loc["reactions"]["total"], 1)
        self.assertEqual(df.loc["reactions_from_me"]["total"], 0)
        self.assertEqual(df.loc["reactions_from_them"]["total"], 1)

    @patch("ica.output_results")
    @patch("sys.argv", [message_totals.__file__, "-c", "Jane Fernbrook"])
    @freeze_time("2024-01-26 9:00:00")
    def test_day_counts(self, output_results: MagicMock) -> None:
        """should count the number of days according to various criteria"""
        message_totals.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        self.assertEqual(df.loc["days_messaged"]["total"], 8)
        self.assertEqual(df.loc["days_missed"]["total"], 12)
        self.assertEqual(df.loc["days_with_no_reply"]["total"], 6)
