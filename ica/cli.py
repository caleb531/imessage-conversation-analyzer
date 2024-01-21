#!/usr/bin/env python3

import argparse
import contextlib
import importlib.machinery
import importlib.resources
import importlib.util
import os
import os.path

# A module-level flag that is set to True if the
in_cli_mode = False


# Parse user arguments from the command line
def get_cli_args() -> argparse.Namespace:
    global in_cli_mode
    parser = argparse.ArgumentParser()
    # Only accept an analyzer parameter if the CLI has been invoked directly
    if in_cli_mode:
        parser.add_argument(
            "analyzer",
            metavar="analyzer",
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
        "--format",
        "-f",
        choices=("csv",),
        help="an optional export format to output the analyzer results as",
    )

    return parser.parse_args()


# Load the given metric file as a Python module, and return the DataFrame
# provided by its analyze() function
def run_analyzer(analyzer: str) -> None:
    # Check to see if the provided value is the module name of a built-in
    # analyzer, otherwise the value is an analyzer path
    with contextlib.suppress(ModuleNotFoundError):
        if importlib.util.find_spec(f"ica.analyzers.{analyzer}"):
            analyzer = str(
                importlib.resources.files(__package__).joinpath(
                    f"analyzers/{analyzer}.py"
                )
            )
    loader = importlib.machinery.SourceFileLoader("analyzer", analyzer)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec:
        analyzer_module = importlib.util.module_from_spec(spec)
        # Expose package information to dynamically-imported module
        analyzer_module.__package__ = __package__
        loader.exec_module(analyzer_module)
        analyzer_module.main()
    else:
        return None


# Program entry point
def main() -> None:
    global in_cli_mode
    if not in_cli_mode:
        in_cli_mode = True

    cli_args = get_cli_args()

    try:
        run_analyzer(cli_args.analyzer)
    except KeyboardInterrupt:
        print("")


if __name__ == "__main__":
    main()
