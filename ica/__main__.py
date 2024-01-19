#!/usr/bin/env python3

import argparse
import os
import os.path

import ica.analyzer as analyzer
import ica.contact as contact


# Parse user arguments from the command line
def get_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contact-name", "-c", required=True)
    parser.add_argument("--metric-file", "-m", type=os.path.expanduser, required=True)
    parser.add_argument("--format", "-f", choices=("csv",))

    return parser.parse_args()


# Program entry point
def main() -> None:
    cli_args = get_cli_args()

    chat_identifiers = contact.get_chat_identifiers(contact_name=cli_args.contact_name)

    try:
        analyzer.analyze_conversation(
            chat_identifiers=chat_identifiers,
            metric_file=cli_args.metric_file,
            format=cli_args.format,
        )
    except KeyboardInterrupt:
        print("")


if __name__ == "__main__":
    main()
