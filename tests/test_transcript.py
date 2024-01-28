#!/usr/bin/env python3
"""test the transcript built-in analyzer"""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from nose2.tools.decorators import with_setup, with_teardown

import ica.analyzers.transcript as transcript
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [transcript.__file__, "-c", "Jane Doe", "-t", "UTC"])
def test_transcript_1(output_results: MagicMock) -> None:
    """should generate a transcript of the first mock conversation"""
    transcript.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    case.assertListEqual(
        df.to_dict(orient="records"),
        pd.read_json("tests/data/transcript-1.json").to_dict(orient="records"),
    )


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [transcript.__file__, "-c", "James Doe", "-t", "UTC"])
def test_transcript_2(output_results: MagicMock) -> None:
    """should generate a transcript of the second mock conversation"""
    transcript.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    case.assertListEqual(
        df.to_dict(orient="records"),
        pd.read_json("tests/data/transcript-2.json").to_dict(orient="records"),
    )
