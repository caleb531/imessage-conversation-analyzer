#!/usr/bin/env python3
"""test the cli built-in analyzer"""

import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

import ica.analyzers.message_totals as message_totals
import ica.cli as cli


class TestCLI(unittest.TestCase):
    """
    Test cases for the CLI, ensuring correct behavior for various argument
    combinations and error handling scenarios.
    """

    def tearDown(self) -> None:
        super().tearDown()
        cli.did_user_invoke_cli_directly = False

    @patch("sys.argv", [cli.__file__])
    def test_cli_no_args(self) -> None:
        """Should raise an exception if no arguments are passed to the CLI."""
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            cli.main()

    @patch("sys.argv", [cli.__file__, "-c", "Jane Fernbrook"])
    def test_cli_contact_but_no_analyzer(self) -> None:
        """Should raise an exception if contact is supplied but no analyzer."""
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            cli.main()

    @patch("sys.argv", [cli.__file__, "message_totals"])
    def test_cli_analyzer_but_no_contact(self) -> None:
        """Should raise an exception if analyzer is supplied but no contact."""
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            cli.main()

    def test_cli_run_built_in_analyzer(self) -> None:
        """Should run built-in analyzer by name."""
        cli_arg_list = ["-c", "Jane Fernbrook"]
        with patch("sys.argv", [cli.__file__, "message_totals", *cli_arg_list]):
            with redirect_stdout(StringIO()) as actual_out:
                cli.main()
                cli.did_user_invoke_cli_directly = False
        with patch("sys.argv", [cli.__file__, *cli_arg_list]):
            with redirect_stdout(StringIO()) as expected_out:
                message_totals.main()
        self.assertEqual(actual_out.getvalue(), expected_out.getvalue())

    def test_cli_run_analyzer_via_path(self) -> None:
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
        self.assertEqual(actual_out.getvalue(), expected_out.getvalue())

    @patch("importlib.util.spec_from_loader", return_value=None)
    def test_cli_spec_error(self, spec_from_loader: MagicMock) -> None:
        """Should raise error when spec cannot be created for analyzer."""
        cli_arg_list = ["-c", "Jane Fernbrook"]
        with patch(
            "sys.argv", [cli.__file__, "ica/analyzers/message_totals.py", *cli_arg_list]
        ):
            with self.assertRaises(ImportError):
                cli.main()
            spec_from_loader.assert_called_once()

    @patch("sys.argv", [cli.__file__, "message_totals", "-c", "Evelyn Oakhaven"])
    def test_cli_conversation_not_found(self) -> None:
        """Should print an error message if conversation was not found."""
        with redirect_stderr(StringIO()) as out, self.assertRaises(SystemExit):
            cli.main()
        self.assertEqual(
            out.getvalue().rstrip(),
            'No conversation found for the contact "Evelyn Oakhaven"',
        )

    @patch("sys.argv", [cli.__file__, "message_totals", "-c", "Imaginary Person"])
    def test_cli_contact_not_found(self) -> None:
        """Should print an error message if contact was not found."""
        with redirect_stderr(StringIO()) as out, self.assertRaises(SystemExit):
            cli.main()
        self.assertEqual(
            out.getvalue().rstrip(), 'No contact found with the name "Imaginary Person"'
        )

    @patch("importlib.util.spec_from_loader", side_effect=KeyboardInterrupt())
    @patch("sys.argv", [cli.__file__, "message_totals", "-c", "Jane Fernbrook"])
    def test_keyboardinterrupt(self, spec_from_loader: MagicMock) -> None:
        """Should print a newline when user presses control-C."""
        with redirect_stdout(StringIO()) as stdout:
            cli.main()
        self.assertEqual(stdout.getvalue(), "\n")

    @patch("sys.argv", [cli.__file__, "-c", "Jane Fernbrook", "message_totals"])
    def test_cli_get_cli_args(self) -> None:
        """Should call the deprecated get_cli_args() function."""
        # Ensure that CLI is run so did_user_invoke_cli_directly is set to True
        with redirect_stdout(StringIO()):
            cli.main()
        cli_args = cli.get_cli_args()
        self.assertEqual(cli_args.contact_name, sys.argv[2])
        self.assertEqual(cli_args.analyzer, sys.argv[3])
