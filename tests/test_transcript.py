#!/usr/bin/env python3
"""test the transcript built-in analyzer"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

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
        rel = output_results.call_args[0][0]
        data = [dict(zip(rel.columns, row)) for row in rel.fetchall()]

        expected = json.loads(
            Path(f"tests/data/transcript-{transcript_num}.json").read_text()
        )

        # Normalize timestamps
        for item in data:
            ts = item["timestamp"]
            # Match the JSON format: 2024-01-07T16:49:39.000Z
            item["timestamp"] = ts.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        assert data == expected
