#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import unittest
from unittest.mock import MagicMock, patch

from freezegun import freeze_time
from nose2.tools.decorators import with_setup, with_teardown

import ica.analyzers.message_totals as message_totals
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Doe"])
def test_message_counts(output_results: MagicMock) -> None:
    """should count the number of messages according to various criteria"""
    message_totals.main()
    df = output_results.call_args[0][0]
    case.assertEqual(df.loc["messages"]["total"], 9)
    case.assertEqual(df.loc["messages_from_me"]["total"], 5)
    case.assertEqual(df.loc["messages_from_them"]["total"], 4)


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Doe"])
def test_reaction_counts(output_results: MagicMock) -> None:
    """should count the number of reactions according to various criteria"""
    message_totals.main()
    df = output_results.call_args[0][0]
    case.assertEqual(df.loc["reactions"]["total"], 0)
    case.assertEqual(df.loc["reactions_from_me"]["total"], 0)
    case.assertEqual(df.loc["reactions_from_them"]["total"], 0)


@with_setup(set_up)
@with_teardown(tear_down)
@patch("ica.output_results")
@patch("sys.argv", [message_totals.__file__, "-c", "Jane Doe"])
@freeze_time("2024-01-26 9:00:00")
def test_day_counts(output_results: MagicMock) -> None:
    """should count the number of days according to various criteria"""
    message_totals.main()
    df = output_results.call_args[0][0]
    case.assertEqual(df.loc["days_messaged"]["total"], 8)
    case.assertEqual(df.loc["days_missed"]["total"], 12)
    case.assertEqual(df.loc["days_with_no_reply"]["total"], 0)
