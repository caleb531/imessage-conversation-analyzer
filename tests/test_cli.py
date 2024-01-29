#!/usr/bin/env python3
"""test the cli built-in analyzer"""

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

from nose2.tools.decorators import with_setup, with_teardown

import ica.analyzers.message_totals as message_totals
import ica.cli as cli
from tests import set_up as set_up_global
from tests import tear_down as tear_down_global

case = unittest.TestCase()


def set_up_cli() -> None:
    """Code to specifically run to set up the CLI"""
    set_up_global()


def tear_down_cli() -> None:
    """Code to specifically run to tear down the CLI"""
    cli.did_user_invoke_cli_directly = False
    tear_down_global()


@with_setup(set_up_cli)
@with_teardown(tear_down_cli)
@patch("sys.argv", [cli.__file__])
def test_cli_no_args() -> None:
    """should raise an exception if no arguments are passed to the CLI"""
    with redirect_stderr(StringIO()), case.assertRaises(SystemExit):
        cli.main()


@with_setup(set_up_cli)
@with_teardown(tear_down_cli)
@patch("sys.argv", [cli.__file__, "-c", "Jane Doe"])
def test_cli_contact_but_no_analyzer() -> None:
    """should raise an exception if contact is supplied but no analyzer"""
    with redirect_stderr(StringIO()), case.assertRaises(SystemExit):
        cli.main()


@with_setup(set_up_cli)
@with_teardown(tear_down_cli)
@patch("sys.argv", [cli.__file__, "message_totals"])
def test_cli_analyzer_but_no_contact() -> None:
    """should raise an exception if analyzer is supplied but no contact"""
    with redirect_stderr(StringIO()), case.assertRaises(SystemExit):
        cli.main()


@with_setup(set_up_cli)
@with_teardown(tear_down_cli)
def test_cli_run_built_in_analyzer() -> None:
    """should run built-in analyzer by name"""
    cli_arg_list = ["-c", "Jane Doe"]
    with patch("sys.argv", [cli.__file__, "message_totals", *cli_arg_list]):
        with redirect_stdout(StringIO()) as actual_out:
            cli.main()
            cli.did_user_invoke_cli_directly = False
    with patch("sys.argv", [cli.__file__, *cli_arg_list]):
        with redirect_stdout(StringIO()) as expected_out:
            message_totals.main()
    case.assertEqual(actual_out.getvalue(), expected_out.getvalue())


@with_setup(set_up_cli)
@with_teardown(tear_down_cli)
def test_cli_run_analyzer_via_path() -> None:
    """should run analyzer via file path"""
    cli_arg_list = ["-c", "Jane Doe"]
    with patch(
        "sys.argv", [cli.__file__, "ica/analyzers/message_totals.py", *cli_arg_list]
    ):
        with redirect_stdout(StringIO()) as actual_out:
            cli.main()
            cli.did_user_invoke_cli_directly = False
    with patch("sys.argv", [cli.__file__, *cli_arg_list]):
        with redirect_stdout(StringIO()) as expected_out:
            message_totals.main()
    case.assertEqual(actual_out.getvalue(), expected_out.getvalue())


@with_setup(set_up_cli)
@with_teardown(tear_down_cli)
@patch("sys.argv", [cli.__file__, "message_totals", "-c", "Imaginary Person"])
def test_cli_contact_not_found() -> None:
    """should print an error message if contact was not found"""
    with redirect_stderr(StringIO()) as out, case.assertRaises(SystemExit):
        cli.main()
    case.assertEqual(
        out.getvalue().rstrip(), 'No contact found with the name "Imaginary Person"'
    )


@with_setup(set_up_cli)
@with_teardown(tear_down_cli)
@patch("importlib.util.spec_from_loader", side_effect=KeyboardInterrupt())
@patch("sys.argv", [cli.__file__, "message_totals", "-c", "Jane Doe"])
def test_keyboardinterrupt(spec_from_loader: MagicMock) -> None:
    """should print a newline when user presses control-C"""
    with redirect_stdout(StringIO()) as out:
        cli.main()
    case.assertEqual(out.getvalue(), "\n")
