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


def get_file_extension_from_format(format: str) -> str:
    """
    map the output format type to the specific file extension used for mock data
    """
    if format == "default":
        return "txt"
    else:
        return format


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
    ext = get_file_extension_from_format(format)
    case.assertEqual(
        out.getvalue().rstrip(),
        Path(f"tests/data/output/{format}/output_results_default_index.{ext}")
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
    ext = get_file_extension_from_format(format)
    case.assertEqual(
        out.getvalue().rstrip(),
        Path(f"tests/data/output/{format}/output_results_labels_in_index.{ext}")
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
    ext = get_file_extension_from_format(format)
    case.assertEqual(
        out.getvalue().rstrip(),
        Path(f"tests/data/output/{format}/output_results_date_index.{ext}")
        .read_text()
        .rstrip(),
    )
