#!/usr/bin/env python3
"""test the transcript built-in analyzer"""

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
from nose2.tools import params
from nose2.tools.decorators import with_setup, with_teardown

import ica.analyzers.transcript as transcript
from tests import set_up, tear_down

case = unittest.TestCase()


@params((1, "Jane Fernbrook"), (2, "Thomas Riverstone"))
@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
def test_transcripts(
    transcript_num: Any, contact_name: str, output_results: MagicMock
) -> None:
    """should generate transcripts of all mock conversations"""
    with patch("sys.argv", [transcript.__file__, "-c", contact_name, "-t", "UTC"]):
        transcript.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        case.assertListEqual(
            df.to_dict(orient="records"),
            pd.read_json(f"tests/data/transcript-{transcript_num}.json").to_dict(
                orient="records"
            ),
        )
