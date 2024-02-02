#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import unittest
from collections.abc import Generator
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pandas as pd

import ica
from ica import assign_lambda

case = unittest.TestCase()

# A series of tuples representing the output types; the first element of each
# type is the format name, and the second element is the file extension
output_types = ((None, "txt"), ("csv", "csv"), ("markdown", "md"))

test_cases = {
    "default_index": pd.DataFrame(
        {
            "first": ["Steven", "Wes", "Martin"],
            "last": ["Spielberg", "Anderson", "Scorsese"],
        }
    ),
    "labels_in_index": pd.DataFrame(
        {
            "metric": ["Messages", "Reactions", "Attachments"],
            "total": [987, 654, 321],
        },
    ).set_index("metric"),
    "date_index": pd.DataFrame(
        {
            "date": ["2024-01-26", "2024-01-27", "2024-01-28"],
            "total": [12, 45, 56],
        },
    )
    .assign(date=assign_lambda(lambda df: pd.to_datetime(df["date"])))
    .set_index("date"),
}


def test_output_results() -> Generator:
    """should output a DataFrame under various cases"""
    for test_name, df in test_cases.items():
        for format, ext in output_types:
            with redirect_stdout(StringIO()) as out:
                ica.output_results(df, format=format)
            yield (
                case.assertEqual,
                out.getvalue().rstrip(),
                Path(f"tests/data/output/{ext}/output_results_{test_name}.{ext}")
                .read_text()
                .rstrip(),
            )
