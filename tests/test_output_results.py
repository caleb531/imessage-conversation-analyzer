#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pandas as pd
from nose2.tools import params

import ica

case = unittest.TestCase()


@params("default", "csv")
def test_output_results_default_index(format: str) -> None:
    """should output a DataFrame with a default index"""
    with redirect_stdout(StringIO()) as out:
        ica.output_results(
            pd.DataFrame(
                {
                    "first": ["Steven", "Wes", "Martin"],
                    "last": ["Spielberg", "Anderson", "Scorsese"],
                }
            ),
            format=format,
        )
    case.assertEqual(
        out.getvalue().rstrip(),
        Path(f"tests/data/output/{format}/output_results_default_index.txt")
        .read_text()
        .rstrip(),
    )


@params("default", "csv")
def test_output_results_labels_in_index(format: str) -> None:
    """should output a DataFrame with a default index"""
    with redirect_stdout(StringIO()) as out:
        ica.output_results(
            pd.DataFrame(
                {
                    "metric": ["Messages", "Reactions", "Attachments"],
                    "total": [987, 654, 321],
                },
            ).pipe(lambda df: df.set_index("metric")),
            format=format,
        )
    case.assertEqual(
        out.getvalue().rstrip(),
        Path(f"tests/data/output/{format}/output_results_labels_in_index.txt")
        .read_text()
        .rstrip(),
    )


@params("default", "csv")
def test_output_results_date_index(format: str) -> None:
    """should output a DataFrame with a default index"""
    with redirect_stdout(StringIO()) as out:
        ica.output_results(
            pd.DataFrame(
                {
                    "date": ["2024-01-26", "2024-01-27", "2024-01-28"],
                    "total": [12, 45, 56],
                },
            )
            .assign(date=lambda df: pd.to_datetime(df["date"]))
            .pipe(lambda df: df.set_index("date")),
            format=format,
        )
    case.assertEqual(
        out.getvalue().rstrip(),
        Path(f"tests/data/output/{format}/output_results_date_index.txt")
        .read_text()
        .rstrip(),
    )
