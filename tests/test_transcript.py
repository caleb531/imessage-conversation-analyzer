#!/usr/bin/env python3
"""test the transcript built-in analyzer"""

from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest

import ica.analyzers.transcript as transcript


@pytest.mark.parametrize(
    ("transcript_num", "contact"),
    [(1, "Jane Fernbrook"), (2, "Thomas Riverstone")],
)
def test_transcripts(transcript_num: Any, contact: str) -> None:
    """Should generate transcripts of all mock conversations."""
    with (
        patch("ica.output_results") as output_results,
        patch("sys.argv", [transcript.__file__, "-c", contact, "-t", "UTC"]),
    ):
        transcript.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        assert df.to_dict(orient="records") == pd.read_json(
            f"tests/data/transcript-{transcript_num}.json"
        ).to_dict(orient="records")
