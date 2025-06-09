#!/usr/bin/env python3
"""test the count_phrases built-in analyzer"""

import sys
from unittest.mock import MagicMock, patch

import pandas as pd

import ica.analyzers.count_phrases as count_phrases
from tests import ICATestCase


class TestMessageTotals(ICATestCase):

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [count_phrases.__file__, "-c", "Thomas Riverstone", "reminds me"],
    )
    def test_single_phrase(self, output_results: MagicMock) -> None:
        """should count the number of occurrences of a single phrase"""
        count_phrases.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        phrase = sys.argv[-1]
        self.assertEqual(df.loc[phrase]["count"], 2)

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [count_phrases.__file__, "-c", "Thomas Riverstone", "-i", "hey", "reminds me"],
    )
    def test_multiple_phrases(self, output_results: MagicMock) -> None:
        """should count the number of occurrences of multiple phrases"""
        count_phrases.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        phrases = sys.argv[-2:]
        self.assertEqual(df.loc[phrases[0]]["count"], 2)
        self.assertEqual(df.loc[phrases[1]]["count"], 2)

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [count_phrases.__file__, "-c", "Thomas Riverstone", "🤣", "😅"],
    )
    def test_emoji(self, output_results: MagicMock) -> None:
        """should count the number of occurrences of the specified emoji"""
        count_phrases.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        phrases = sys.argv[-2:]
        self.assertEqual(df.loc[phrases[0]]["count"], 2)
        self.assertEqual(df.loc[phrases[0]]["count_from_me"], 1)
        self.assertEqual(df.loc[phrases[0]]["count_from_them"], 1)
        self.assertEqual(df.loc[phrases[1]]["count"], 1)
        self.assertEqual(df.loc[phrases[1]]["count_from_me"], 0)
        self.assertEqual(df.loc[phrases[1]]["count_from_them"], 1)

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [count_phrases.__file__, "-c", "Jane Fernbrook", " "],
    )
    def test_whitespace(self, output_results: MagicMock) -> None:
        """should count the number of occurrences of a space character"""
        count_phrases.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        phrase = sys.argv[-1]
        self.assertEqual(df.loc[phrase]["count"], 90)
        self.assertEqual(df.loc[phrase]["count_from_me"], 43)
        self.assertEqual(df.loc[phrase]["count_from_them"], 47)

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [count_phrases.__file__, "-c", "Thomas Riverstone", "!"],
    )
    def test_special_characters(self, output_results: MagicMock) -> None:
        """should count the number of occurrences of a special character"""
        count_phrases.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        phrase = sys.argv[-1]
        self.assertEqual(df.loc[phrase]["count"], 10)
        self.assertEqual(df.loc[phrase]["count_from_me"], 5)
        self.assertEqual(df.loc[phrase]["count_from_them"], 5)

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [count_phrases.__file__, "-c", "Thomas Riverstone", "--use-regex", "🤣|😅"],
    )
    def test_regex(self, output_results: MagicMock) -> None:
        """
        should count the number of occurrences of strings matching a regular
        expression
        """
        count_phrases.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        phrase = sys.argv[-1]
        self.assertEqual(df.loc[phrase]["count"], 3)
        self.assertEqual(df.loc[phrase]["count_from_me"], 1)
        self.assertEqual(df.loc[phrase]["count_from_them"], 2)
