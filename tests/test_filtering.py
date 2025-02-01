#!/usr/bin/env python3
"""test the ability to filter analyzer results by date and person"""

from unittest.mock import MagicMock, patch

import pandas as pd

import ica
import ica.analyzers.totals_by_day as totals_by_day
from tests import ICATestCase


class TestFiltering(ICATestCase):

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [
            totals_by_day.__file__,
            "-c",
            "Jane Fernbrook",
            "-t",
            "UTC",
            "--from-date",
            "2024-01-11",
        ],
    )
    def test_from_date(self, output_results: MagicMock) -> None:
        """
        should filter the results to those sent at or after the specified date
        """
        totals_by_day.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        expected_dates = [
            "2024-01-11",
            "2024-01-14",
            "2024-01-16",
            "2024-01-17",
            "2024-01-19",
        ]
        self.assertEqual(
            df.index.tolist(),
            [pd.Timestamp(date, tz="UTC") for date in expected_dates],
        )

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [
            totals_by_day.__file__,
            "-c",
            "Jane Fernbrook",
            "-t",
            "UTC",
            "--to-date",
            "2024-01-17",
        ],
    )
    def test_to_date(self, output_results: MagicMock) -> None:
        """
        should filter the results to those sent before the specified date
        """
        totals_by_day.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        expected_dates = [
            "2024-01-07",
            "2024-01-08",
            "2024-01-09",
            "2024-01-11",
            "2024-01-14",
            "2024-01-16",
        ]
        self.assertEqual(
            df.index.tolist(),
            [pd.Timestamp(date, tz="UTC") for date in expected_dates],
        )

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [
            totals_by_day.__file__,
            "-c",
            "Jane Fernbrook",
            "-t",
            "UTC",
            "--from-date",
            "2024-01-11",
            "--to-date",
            "2024-01-17",
        ],
    )
    def test_date_range(self, output_results: MagicMock) -> None:
        """
        should filter the results to those sent between the specified dates
        """
        totals_by_day.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        expected_dates = [
            "2024-01-11",
            "2024-01-14",
            "2024-01-16",
        ]
        self.assertEqual(
            df.index.tolist(),
            [pd.Timestamp(date, tz="UTC") for date in expected_dates],
        )

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [
            totals_by_day.__file__,
            "-c",
            "Jane Fernbrook",
            "-t",
            "UTC",
            "--from-date",
            "2024-01-17",
            "--to-date",
            "2024-01-11",
        ],
    )
    def test_invalid_date_range(self, output_results: MagicMock) -> None:
        """
        should filter the results to those sent between the specified dates
        """
        with self.assertRaises(ica.DateRangeInvalidError):
            totals_by_day.main()
