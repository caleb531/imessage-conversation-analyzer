#!/usr/bin/env python3

import argparse
import ica.analyzer as analyzer


# Parse user arguments from the command line
def get_cli_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('phone_number')

    return parser.parse_args()


# Program entry point
def main():

    cli_args = get_cli_args()

    try:
        analyzer.run(phone_number=cli_args.phone_number)
    except KeyboardInterrupt:
        print('')


if __name__ == '__main__':
    main()
