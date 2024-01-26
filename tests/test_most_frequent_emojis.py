#!/usr/bin/env python3
"""test the most_frequent_emojis built-in analyzer"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
from nose2.tools.decorators import with_setup, with_teardown

import ica.analyzers.most_frequent_emojis as most_frequent_emojis
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [most_frequent_emojis.__file__, "-c", "Jane Doe"])
def test_most_frequent_emojis(output_results: MagicMock) -> None:
    """should compute the most frequently-used emojis"""
    most_frequent_emojis.__package__ = "ica"
    most_frequent_emojis.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    case.assertEqual(
        df.to_dict("index"),
        json.loads(Path("tests/data/most_frequent_emojis.json").read_text()),
    )
