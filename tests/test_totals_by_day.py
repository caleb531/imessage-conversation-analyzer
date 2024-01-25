#!/usr/bin/env python3
"""test the totals_by_day built-in analyzer"""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from nose2.tools.decorators import with_setup, with_teardown

import ica.analyzers.totals_by_day as totals_by_day
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [totals_by_day.__file__, "-c", "Jane Doe"])
def test_totals_by_day(output_results: MagicMock) -> None:
    """should count the total number of days"""
    totals_by_day.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    case.assertEqual(len(df.index), 12)
    case.assertEqual(
        df.to_dict("index"),
        {
            "2024-01-07": {
                "text": 1,
                "is_from_me": 1,
                "is_reaction": 0,
                "is_from_them": 0,
            },
            "2024-01-08": {
                "text": 1,
                "is_from_me": 0,
                "is_reaction": 0,
                "is_from_them": 1,
            },
            "2024-01-09": {
                "text": 2,
                "is_from_me": 1,
                "is_reaction": 0,
                "is_from_them": 1,
            },
            "2024-01-10": {
                "text": 0,
                "is_from_me": 0,
                "is_reaction": 0,
                "is_from_them": 0,
            },
            "2024-01-11": {
                "text": 2,
                "is_from_me": 1,
                "is_reaction": 1,
                "is_from_them": 1,
            },
            "2024-01-12": {
                "text": 0,
                "is_from_me": 0,
                "is_reaction": 0,
                "is_from_them": 0,
            },
            "2024-01-13": {
                "text": 0,
                "is_from_me": 0,
                "is_reaction": 0,
                "is_from_them": 0,
            },
            "2024-01-14": {
                "text": 1,
                "is_from_me": 0,
                "is_reaction": 0,
                "is_from_them": 1,
            },
            "2024-01-15": {
                "text": 0,
                "is_from_me": 0,
                "is_reaction": 0,
                "is_from_them": 0,
            },
            "2024-01-16": {
                "text": 1,
                "is_from_me": 1,
                "is_reaction": 0,
                "is_from_them": 0,
            },
            "2024-01-17": {
                "text": 1,
                "is_from_me": 0,
                "is_reaction": 0,
                "is_from_them": 1,
            },
            "2024-01-18": {
                "text": 1,
                "is_from_me": 1,
                "is_reaction": 0,
                "is_from_them": 0,
            },
        },
    )
