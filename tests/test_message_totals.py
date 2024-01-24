#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import unittest
from unittest.mock import MagicMock, patch

from nose2.tools.decorators import with_setup, with_teardown

import ica.analyzers.message_totals as message_totals
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Doe"])
def test_message_count(output_results: MagicMock) -> None:
    message_totals.main()
    df = output_results.call_args[0][0]
    # Messages
    case.assertEqual(df.iloc[0]["total"], 9)
    # Messages From Me
    case.assertEqual(df.iloc[1]["total"], 5)
    # Messages From Them
    case.assertEqual(df.iloc[2]["total"], 4)
    # Reactions
    case.assertEqual(df.iloc[3]["total"], 0)
    # Reactions From Me
    case.assertEqual(df.iloc[4]["total"], 0)
    # Reactions From Them
    case.assertEqual(df.iloc[5]["total"], 0)
    # Days Messaged
    case.assertEqual(df.iloc[6]["total"], 11)
    # Days Missed
    case.assertEqual(df.iloc[7]["total"], -11)
    # Days With No Reply
    case.assertEqual(df.iloc[8]["total"], 14)
