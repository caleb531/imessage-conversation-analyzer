#!/usr/bin/env python3
"""test the most_frequent_emojis built-in analyzer"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

import ica.analyzers.most_frequent_emojis as most_frequent_emojis
from tests import ICATestCase


class TestMostFrequentEmojis(ICATestCase):

    @patch("ica.output_results")
    @patch("sys.argv", [most_frequent_emojis.__file__, "-c", "Jane Fernbrook"])
    def test_most_frequent_emojis(self, output_results: MagicMock) -> None:
        """should compute the most frequently-used emojis"""
        most_frequent_emojis.__package__ = "ica"
        most_frequent_emojis.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        self.assertEqual(
            df.to_dict("index"),
            json.loads(Path("tests/data/most_frequent_emojis.json").read_text()),
        )

    @patch("ica.output_results")
    @patch("sys.argv", [most_frequent_emojis.__file__, "-c", "Daniel Brightingale"])
    def test_skin_tones(self, output_results: MagicMock) -> None:
        """should disregard skin tones when counting emojis"""
        most_frequent_emojis.__package__ = "ica"
        most_frequent_emojis.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        self.assertEqual(df.loc["👍"]["count"], 6)
