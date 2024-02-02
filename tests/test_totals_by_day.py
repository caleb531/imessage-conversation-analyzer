#!/usr/bin/env python3
"""test the totals_by_day built-in analyzer"""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from nose2.tools.decorators import with_setup, with_teardown

import ica.analyzers.totals_by_day as totals_by_day
from ica import pipe_lambda
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [totals_by_day.__file__, "-c", "Jane Fernbrook", "-t", "UTC"])
def test_totals_by_day(output_results: MagicMock) -> None:
    """should count the total number of days"""
    totals_by_day.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    case.assertEqual(
        df.to_dict(orient="index"),
        pd.read_json("tests/data/totals_by_day.json", orient="index")
        # ICA provides timezone-aware date/times, however the date/time objects
        # parsed from the JSON are missing timezone information (i.e. they are
        # timezone-naive); therefore, we must add the missing timezone
        # information (note that this does not perform any conversions)
        .pipe(
            pipe_lambda(lambda df: df.set_index(df.index.tz_localize("UTC")))
        ).to_dict(
            orient="index",
        ),
    )
