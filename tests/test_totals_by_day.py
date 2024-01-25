#!/usr/bin/env python3
"""test the totals_by_day built-in analyzer"""

import unittest
from unittest.mock import MagicMock, patch

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
    df = output_results.call_args[0][0]
    case.assertEqual(len(df.index), 12)
