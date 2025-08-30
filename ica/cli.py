#!/usr/bin/env python3

import argparse
import contextlib
import importlib.machinery
import importlib.resources
import importlib.util
import os
import os.path
import sys

from ica.exceptions import BaseAnalyzerException

# A module-level flag that is set to True if the user invokes the CLI via the
# `ica` command, meaning that an `analyzer` argument will need to be specified
# as a required CLI argument; otherwise, if the user executes an analyzer file
# directly (via `python`, `python -m`, or as an executable), then there is no
# need for the additional CLI argument because it's intrinsically represented by
# the file being executed
did_user_invoke_cli_directly = False


def get_cli_parser() -> argparse.ArgumentParser:
    """
    Retrieve the instance of the parser used to parse user arguments
    from the command line
    """
    global did_user_invoke_cli_directly
    parser = argparse.ArgumentParser()
    # Only accept an analyzer parameter if the user is interacting with the CLI
    # through the `ica` command
    if did_user_invoke_cli_directly:
        parser.add_argument(
            "analyzer",
            type=os.path.expanduser,
            help="the name of a built-in analyzer, or a path to an analyzer file",
        )
    parser.add_argument(
        "--contact-name",
        "-c",
        required=True,
        help="the full name of a macOS contact whose conversation you want to analyze",
    )
    parser.add_argument(
        "--timezone",
        "-t",
        help="the IANA time zone name to use for dates; "
        "defaults to the system's local time zone",
    )
    parser.add_argument(
        "--from-date",
        help="a start date to filter messages by (inclusive); the format must "
        "be ISO 8601-compliant, e.g. YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS",
    )
    parser.add_argument(
        "--to-date",
        help="an end date to filter messages by (exclusive); the format must be"
        " ISO 8601-compliant, e.g. YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS",
    )
    parser.add_argument(
        "--from-person",
        choices=["me", "them", "both"],
        help="A reference to the person by whom to filter messages; accepted "
        "values can be 'me', 'them', or 'both' (the default)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=(
            "csv",
            "md",
            "markdown",
            "xlsx",
            "excel",
        ),
        help="an optional export format to output the analyzer results as",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="the path of the file to export analyzer results to; required when"
        " exporting Excel (xlsx) files",
    )

    return parser


# Retrieve the file path of a module given its module path (e.g. "ica.analyzers.message_totals")
def get_file_path_from_module_path(module_name: str) -> str:
    spec = importlib.util.find_spec(module_name)
    if spec is None or spec.origin is None or spec.origin == "namespace":
        raise ModuleNotFoundError(module_name)
    return spec.origin


def get_cli_args() -> argparse.Namespace:
    """
    [DEPRECATED]: Parse user arguments from the command line; use
    get_cli_parser().parse_args() instead
    """
    return get_cli_parser().parse_args()


def run_analyzer(analyzer: str) -> None:
    """
    Load the given metric file as a Python module, and return the DataFrame
    provided by its analyze() function
    """
    # Check to see if the provided value is the module name of a built-in
    # analyzer, otherwise the value is an analyzer path
    with contextlib.suppress(ModuleNotFoundError):
        analyzer = get_file_path_from_module_path(f"ica.analyzers.{analyzer}").replace(
            "__init__.py", "__main__.py"
        )
    loader = importlib.machinery.SourceFileLoader("__main__", analyzer)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if not spec:
        raise ImportError(f"Could not create a module spec for {analyzer}")
    analyzer_module = importlib.util.module_from_spec(spec)
    # Expose package information to dynamically-imported module
    analyzer_module.__package__ = __package__
    loader.exec_module(analyzer_module)


def main() -> None:
    """
    Entry point for the `ica` CLI command
    """
    # Keep track of whether the user invokes the CLI directly via the `ica`
    # command
    global did_user_invoke_cli_directly
    did_user_invoke_cli_directly = True

    # parse_known_args() is slightly different from parse_args() in that the
    # former returns a two-item tuple where the first item is the Namespace of
    # known arguments, and the second item is a list of any unknown arguments
    cli_args = get_cli_parser().parse_known_args()[0]

    try:
        run_analyzer(cli_args.analyzer)
    except BaseAnalyzerException as error:
        # Print the error message without the traceback
        print(error, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("")


if __name__ == "__main__":
    main()
