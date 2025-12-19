#!/usr/bin/env python3
"""test the totals_by_day built-in analyzer"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import ica.analyzers.totals_by_day as totals_by_day


@patch("ica.output_results")
@patch("sys.argv", [totals_by_day.__file__, "-c", "Jane Fernbrook", "-t", "UTC"])
def test_totals_by_day(output_results: MagicMock) -> None:
    """Should count the total number of days."""
    totals_by_day.main()
    rel = output_results.call_args[0][0]
    data = [dict(zip(rel.columns, row)) for row in rel.fetchall()]
    result = {
        item["date"]: {k: v for k, v in item.items() if k != "date"} for item in data
    }

    expected_raw = json.loads(Path("tests/data/totals_by_day.json").read_text())
    expected = {k[:10]: v for k, v in expected_raw.items()}

    assert result == expected
