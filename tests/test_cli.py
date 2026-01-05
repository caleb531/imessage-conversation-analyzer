#!/usr/bin/env python3
"""test the cli built-in analyzer"""

import importlib.metadata
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

import ica.analyzers.message_totals as message_totals
import ica.cli as cli


def teardown_function() -> None:
    """Reset CLI state after each test."""
    cli.did_user_invoke_cli_directly = False


@patch("sys.argv", [cli.__file__])
def test_cli_no_args() -> None:
    """Should raise an exception if no arguments are passed to the CLI."""
    with redirect_stderr(StringIO()), pytest.raises(SystemExit):
        cli.main()


@patch("sys.argv", [cli.__file__, "-c", "Jane Fernbrook"])
def test_cli_contact_but_no_analyzer() -> None:
    """Should raise an exception if contact is supplied but no analyzer."""
    with redirect_stderr(StringIO()), pytest.raises(SystemExit):
        cli.main()


@patch("sys.argv", [cli.__file__, "message_totals"])
def test_cli_analyzer_but_no_contact() -> None:
    """Should raise an exception if analyzer is supplied but no contact."""
    with redirect_stderr(StringIO()), pytest.raises(SystemExit):
        cli.main()


def test_cli_run_built_in_analyzer() -> None:
    """Should run built-in analyzer by name."""
    cli_arg_list = ["-c", "Jane Fernbrook"]
    with patch("sys.argv", [cli.__file__, "message_totals", *cli_arg_list]):
        with redirect_stdout(StringIO()) as actual_out:
            cli.main()
            cli.did_user_invoke_cli_directly = False
    with patch("sys.argv", [cli.__file__, *cli_arg_list]):
        with redirect_stdout(StringIO()) as expected_out:
            message_totals.main()
    assert actual_out.getvalue() == expected_out.getvalue()


def test_cli_run_analyzer_via_path() -> None:
    """Should run analyzer via file path."""
    cli_arg_list = ["-c", "Jane Fernbrook"]
    with patch(
        "sys.argv", [cli.__file__, "ica/analyzers/message_totals.py", *cli_arg_list]
    ):
        with redirect_stdout(StringIO()) as actual_out:
            cli.main()
            cli.did_user_invoke_cli_directly = False
    with patch("sys.argv", [cli.__file__, *cli_arg_list]):
        with redirect_stdout(StringIO()) as expected_out:
            message_totals.main()
    assert actual_out.getvalue() == expected_out.getvalue()


@patch("importlib.util.find_spec", return_value=None)
@patch("importlib.util.spec_from_loader", return_value=None)
def test_cli_spec_error(find_spec: MagicMock, spec_from_loader: MagicMock) -> None:
    """Should raise error when spec cannot be created for analyzer."""
    cli_arg_list = ["-c", "Jane Fernbrook"]
    with patch(
        "sys.argv", [cli.__file__, "ica/analyzers/message_totals.py", *cli_arg_list]
    ):
        with pytest.raises(ImportError):
            cli.main()
        find_spec.assert_called_once()
        spec_from_loader.assert_called_once()


@patch("sys.argv", [cli.__file__, "message_totals", "-c", "Evelyn Oakhaven"])
def test_cli_conversation_not_found() -> None:
    """Should print an error message if conversation was not found."""
    with redirect_stderr(StringIO()) as out, pytest.raises(SystemExit):
        cli.main()
    assert (
        out.getvalue().rstrip()
        == 'No conversation found for the contact(s) "Evelyn Oakhaven"'
    )


@patch("sys.argv", [cli.__file__, "message_totals", "-c", "Imaginary Person"])
def test_cli_contact_not_found() -> None:
    """Should print an error message if contact was not found."""
    with redirect_stderr(StringIO()) as out, pytest.raises(SystemExit):
        cli.main()
    assert out.getvalue().rstrip() == "No contact found for Imaginary Person"


@patch("importlib.util.spec_from_loader", side_effect=KeyboardInterrupt())
@patch("sys.argv", [cli.__file__, "message_totals", "-c", "Jane Fernbrook"])
def test_keyboardinterrupt(spec_from_loader: MagicMock) -> None:
    """Should print a newline when user presses control-C."""
    with redirect_stdout(StringIO()) as out:
        cli.main()
    assert out.getvalue() == "\n"


@patch("sys.argv", [cli.__file__, "message_totals", "-c", "Jane Fernbrook"])
def test_cli_get_cli_args() -> None:
    """Should call the deprecated get_cli_args() function."""
    # Ensure that CLI is run so did_user_invoke_cli_directly is set to True
    with redirect_stdout(StringIO()):
        cli.main()
    cli_args = cli.get_cli_args()
    assert cli_args.contacts == [sys.argv[3]]
    assert cli_args.analyzer == sys.argv[1]


@patch("importlib.metadata.version", return_value="1.2.3")
@patch("sys.argv", [cli.__file__, "--version"])
def test_cli_version(mock_version: MagicMock) -> None:
    """Should print the version number."""
    with redirect_stdout(StringIO()) as out, pytest.raises(SystemExit):
        cli.main()
    assert "1.2.3" in out.getvalue()


@patch(
    "importlib.metadata.version",
    side_effect=importlib.metadata.PackageNotFoundError,
)
@patch("sys.argv", [cli.__file__, "--version"])
def test_cli_version_fallback(mock_version: MagicMock) -> None:
    """Should print 0.0.0 if package version cannot be obtained."""
    with redirect_stdout(StringIO()) as out, pytest.raises(SystemExit):
        cli.main()
    assert "0.0.0" in out.getvalue()
