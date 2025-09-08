#!/usr/bin/env python3
"""test the ability to filter analyzer results by date and person"""

from unittest.mock import MagicMock, patch

import pandas as pd

import ica
import ica.analyzers.attachment_totals as attachment_totals
import ica.analyzers.totals_by_day as totals_by_day
from tests.utils import ICATestCase


class TestFiltering(ICATestCase):
    """
    Test cases for filtering analyzer results by date and person, ensuring
    correct handling of various filtering criteria.
    """

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
        Should filter the results to those sent at or after the specified date.
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
        Should filter the results to those sent before the specified date.
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
        Should filter the results to those sent between the specified dates.
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
        Should filter the results to those sent between the specified dates.
        """
        with self.assertRaises(ica.DateRangeInvalidError):
            totals_by_day.main()

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [
            attachment_totals.__file__,
            "-c",
            "Thomas Riverstone",
            "-t",
            "UTC",
            "--from-person",
            "me",
        ],
    )
    def test_from_person_me(self, output_results: MagicMock) -> None:
        """
        Should filter the results to those sent by the person running the
        command.
        """
        attachment_totals.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        self.assertEqual(df.loc["youtube_videos"]["total"], 1)
        self.assertEqual(df.loc["apple_music"]["total"], 1)
        self.assertEqual(df.loc["spotify"]["total"], 1)

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [
            attachment_totals.__file__,
            "-c",
            "Thomas Riverstone",
            "-t",
            "UTC",
            "--from-person",
            "them",
        ],
    )
    def test_from_person_them(self, output_results: MagicMock) -> None:
        """
        Should filter the results to those sent by the other participant.
        """
        attachment_totals.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        self.assertEqual(df.loc["youtube_videos"]["total"], 3)
        self.assertEqual(df.loc["apple_music"]["total"], 0)
        self.assertEqual(df.loc["spotify"]["total"], 0)

    @patch("ica.output_results")
    @patch(
        "sys.argv",
        [
            attachment_totals.__file__,
            "-c",
            "Thomas Riverstone",
            "-t",
            "UTC",
            "--from-person",
            "both",
        ],
    )
    def test_from_person_both(self, output_results: MagicMock) -> None:
        """
        Should filter the results to those sent by either participant (i.e. no
        filtering is applied).
        """
        attachment_totals.main()
        df: pd.DataFrame = output_results.call_args[0][0]
        self.assertEqual(df.loc["youtube_videos"]["total"], 4)
        self.assertEqual(df.loc["apple_music"]["total"], 1)
        self.assertEqual(df.loc["spotify"]["total"], 1)
