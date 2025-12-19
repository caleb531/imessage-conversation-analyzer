#!/usr/bin/env python3
"""test the most_frequent_emojis built-in analyzer"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import ica.analyzers.most_frequent_emojis as most_frequent_emojis


@patch("ica.output_results")
@patch("sys.argv", [most_frequent_emojis.__file__, "-c", "Jane Fernbrook"])
def test_most_frequent_emojis(output_results: MagicMock) -> None:
    """Should compute the most frequently-used emojis."""
    most_frequent_emojis.__package__ = "ica"
    most_frequent_emojis.main()
    data = output_results.call_args[0][0]
    result = {item["emoji"]: {"count": item["count"]} for item in data}
    assert result == json.loads(
        Path("tests/data/most_frequent_emojis.json").read_text()
    )


@patch("ica.output_results")
@patch(
    "sys.argv",
    [most_frequent_emojis.__file__, "-c", "Jane Fernbrook", "--result-count", "3"],
)
def test_most_frequent_emojis_result_count(output_results: MagicMock) -> None:
    """
    Should compute the n most frequently-used emojis (where n is
    user-specified).
    """
    most_frequent_emojis.__package__ = "ica"
    most_frequent_emojis.main()
    data = output_results.call_args[0][0]
    result = {item["emoji"]: {"count": item["count"]} for item in data}
    assert result == {
        k: v
        for k, v in json.loads(
            Path("tests/data/most_frequent_emojis.json").read_text()
        ).items()
        if k in ["😀", "😊", "👨‍💻"]
    }


@patch("ica.output_results")
@patch("sys.argv", [most_frequent_emojis.__file__, "-c", "Daniel Brightingale"])
def test_skin_tones(output_results: MagicMock) -> None:
    """Should disregard skin tones when counting emojis."""
    most_frequent_emojis.__package__ = "ica"
    most_frequent_emojis.main()
    data = output_results.call_args[0][0]
    count = next((item["count"] for item in data if item["emoji"] == "👍"), 0)
    assert count == 6
