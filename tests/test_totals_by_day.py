#!/usr/bin/env python3
"""test the totals_by_day built-in analyzer"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl

import ica.analyzers.totals_by_day as totals_by_day


@patch("ica.output_results")
@patch("sys.argv", [totals_by_day.__file__, "-c", "Jane Fernbrook", "-t", "UTC"])
def test_totals_by_day(output_results: MagicMock) -> None:
    """Should count the total number of days."""
    totals_by_day.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    
    # Convert dataframe to dict keyed by date string to match JSON
    # The JSON keys are like "2024-01-07T00:00:00.000"
    result_dict = {
        row["date"].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]: {
            k: v for k, v in row.items() if k != "date"
        }
        for row in df.to_dicts()
    }
    
    expected_dict = json.loads(Path("tests/data/totals_by_day.json").read_text())
    assert result_dict == expected_dict
