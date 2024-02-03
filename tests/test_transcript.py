#!/usr/bin/env python3
"""test the transcript built-in analyzer"""

from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
from nose2.tools import params

import ica.analyzers.transcript as transcript
from tests import ICATestCase


class TestTranscript(ICATestCase):

    @params((1, "Jane Fernbrook"), (2, "Thomas Riverstone"))
    @patch("ica.output_results")
    def test_transcripts(
        self, transcript_num: Any, contact_name: str, output_results: MagicMock
    ) -> None:
        """should generate transcripts of all mock conversations"""
        with patch("sys.argv", [transcript.__file__, "-c", contact_name, "-t", "UTC"]):
            transcript.main()
            df: pd.DataFrame = output_results.call_args[0][0]
            self.assertListEqual(
                df.to_dict(orient="records"),
                pd.read_json(f"tests/data/transcript-{transcript_num}.json").to_dict(
                    orient="records"
                ),
            )
