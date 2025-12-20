#!/usr/bin/env python3
"""test the transcript built-in analyzer"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import polars as pl
import pytest

import ica.analyzers.transcript as transcript


@pytest.mark.parametrize(
    ("transcript_num", "contact_name"),
    [(1, "Jane Fernbrook"), (2, "Thomas Riverstone")],
)
def test_transcripts(transcript_num: Any, contact_name: str) -> None:
    """Should generate transcripts of all mock conversations."""
    with (
        patch("ica.output_results") as output_results,
        patch("sys.argv", [transcript.__file__, "-c", contact_name, "-t", "UTC"]),
    ):
        transcript.main()
        df: pl.DataFrame = output_results.call_args[0][0]
        
        # Convert dataframe to list of dicts with formatted timestamp
        actual_data = df.with_columns(
            pl.col("timestamp").dt.strftime("%Y-%m-%dT%H:%M:%S.%3fZ")
        ).to_dicts()
        
        expected_data = json.loads(
            Path(f"tests/data/transcript-{transcript_num}.json").read_text()
        )
        
        assert actual_data == expected_data
