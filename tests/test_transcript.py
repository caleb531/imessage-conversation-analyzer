#!/usr/bin/env python3
"""test the transcript built-in analyzer"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
from nose2.tools.decorators import with_setup, with_teardown

import ica.analyzers.transcript as transcript
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [transcript.__file__, "-c", "Jane Doe"])
def test_transcript(output_results: MagicMock) -> None:
    """should count the total number of days"""
    transcript.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    case.assertListEqual(
        json.loads(df.to_json(orient="records", date_format="iso")),
        json.loads(Path("tests/data/transcript.json").read_text()),
    )
