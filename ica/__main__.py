#!/usr/bin/env python3

import argparse
import os
import os.path
import ica.analyzer as analyzer


# Parse user arguments from the command line
def get_cli_args():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--phone-number',
        '-p',
        required=True)
    parser.add_argument(
        '--metric-file',
        '-m',
        type=os.path.expanduser,
        required=True)
    parser.add_argument(
        '--format',
        '-f',
        choices=('csv'))

    return parser.parse_args()


# Program entry point
def main():

    cli_args = get_cli_args()

    try:
        analyzer.analyze_conversation(**vars(cli_args))
    except KeyboardInterrupt:
        print('')


if __name__ == '__main__':
    main()
