#!/usr/bin/env python3

import argparse
import contextlib
import importlib.machinery
import importlib.metadata
import importlib.util
import sys
from pathlib import Path
from typing import Union

from ica.exceptions import BaseAnalyzerException

# A module-level flag that is set to True if the user invokes the CLI via the
# `ica` command, meaning that an `analyzer` argument will need to be specified
# as a required CLI argument; otherwise, if the user executes an analyzer file
# directly (via `python`, `python -m`, or as an executable), then there is no
# need for the additional CLI argument because it's intrinsically represented by
# the file being executed
did_user_invoke_cli_directly = False


class TypedCLIArguments(object):
    """
    A subclass of argparse.Namespace that exposes type information for all CLI
    arguments supported by the program
    """

    analyzer: str
    contacts: list[str]
    timezone: Union[str, None]
    from_date: Union[str, None]
    to_date: Union[str, None]
    from_person: Union[str, None]
    format: Union[str, None]
    output: Union[str, None]


def get_package_version() -> str:
    """
    Retrieve the current ICA version from the project metadata
    """
    try:
        return importlib.metadata.version("imessage-conversation-analyzer")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


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
            type=lambda p: str(Path(p).expanduser()),
            help="the name of a built-in analyzer, or a path to an analyzer file",
        )
    parser.add_argument(
        "--contacts",
        "-c",
        required=True,
        nargs="+",
        help="the full name(s), phone number(s), or email address(es) of the "
        "macOS contact(s) whose conversation you want to analyze",
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
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_package_version()}",
    )

    return parser


# Retrieve the file path of a module given its module path (e.g.
# "ica.analyzers.message_totals")
def get_file_path_from_module_path(module_name: str) -> str:
    """Construct the file path of a module from its specified module path"""
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
    # former returns a two-item tuple, where the first item is the Namespace of
    # known arguments, and the second item is a list of any unknown arguments
    cli_args = get_cli_parser().parse_known_args(namespace=TypedCLIArguments)[0]

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
