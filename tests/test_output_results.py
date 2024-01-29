#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pandas as pd

import ica

case = unittest.TestCase()


def test_output_results_default_index() -> None:
    """should output a DataFrame with a default index"""
    with redirect_stdout(StringIO()) as out:
        ica.output_results(
            pd.DataFrame(
                {
                    "first": ["Steven", "Wes", "Martin"],
                    "last": ["Spielberg", "Anderson", "Scorsese"],
                }
            )
        )
    case.assertEqual(
        out.getvalue(),
        Path("tests/data/output/output_results_default_index.txt").read_text(),
    )


def test_output_results_labels_in_index() -> None:
    """should output a DataFrame with a default index"""
    with redirect_stdout(StringIO()) as out:
        ica.output_results(
            pd.DataFrame(
                {
                    "metric": ["Messages", "Reactions", "Attachments"],
                    "total": [987, 654, 321],
                },
            ).pipe(lambda df: df.set_index("metric"))
        )
    case.assertEqual(
        out.getvalue(),
        Path("tests/data/output/output_results_labels_in_index.txt").read_text(),
    )


def test_output_results_date_index() -> None:
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
            .pipe(lambda df: df.set_index("date"))
        )
    case.assertEqual(
        out.getvalue(),
        Path("tests/data/output/output_results_date_index.txt").read_text(),
    )
