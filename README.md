# iMessage Conversation Analyzer

*Copyright 2020-2024 Caleb Evans*  
*Released under the MIT license*

[![tests](https://github.com/caleb531/imessage-conversation-analyzer/actions/workflows/tests.yml/badge.svg)](https://github.com/caleb531/imessage-conversation-analyzer/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/caleb531/imessage-conversation-analyzer/badge.svg?branch=main)](https://coveralls.io/r/caleb531/imessage-conversation-analyzer?branch=main)

iMessage Conversation Analyzer (ICA) is a fully-typed Python program that will
read the contents of an iMessage conversation via the Messages app's database on
macOS. You can then gather various metrics of interest on the messages.

Much of this program was inspired by and built using findings from [this blog post by Yorgos Askalidis][blog-post].

[blog-post]: https://towardsdatascience.com/heres-how-you-can-access-your-entire-imessage-history-on-your-mac-f8878276c6e9

### Caveats

Please note that currently, you can only query conversations between you and a
single other person (i.e. group chats are currently unsupported).

It should also be clarified that this program only supports macOS, since the
presence of the chat.db file in your user Library directory is essential for the
program to function.

## Installation

### 1. Install Python 3

To install Python 3, you'll need to install the Apple Command Line Tools, which
you can install by running:

```sh
xcode-select --install
```

Don't worry if you see a long download time; it will shorten rather quickly.

### 2. Set up virtualenv

```sh
pip3 install virtualenv
```

```sh
virtualenv --python=python3 .virtualenv
source .virtualenv/bin/activate
```

### 3. Install project depdendencies

```sh
pip install -r requirements.txt
```

## Usage

The package includes both a Command Line API for simplicity/convenience, as well
as a Python API for maximum flexibility.

### Command Line API

To use ICA from the command line, simply invoke the `ica` command. The minimum required arguments are:

1. A path to an analyzer file to run, or the name of a built-in analyzer
2. The first and last name of the contact, via the `-c`/`--contact` flag
   1. If the contact has no last name on record, you can just pass the first
      name

You can optionally pass the `-f`/`--format` flag to output to a specific format
like CSV (currently, only `csv` is supported).

```sh
ica message_totals -c 'John Doe'
```

```sh
ica ./my_custom_analyzer.py -c 'John Doe'
```

```sh
ica transcript -c 'John Doe' -f csv > ./my_transcript.csv
```

### Python API

The Python API is much more powerful, allowing you to integrate ICA into any
type of Python project that can run on macOS. All of the built-in analyzers
themselves (under the `ica/analyzers` directory) actually use this API.

```python
# get_my_transcript.py

import pandas as pd

import ica


# Export a transcript of the entire conversation
def main() -> None:
    # Allow your program to accept all the same CLI arguments as the `ica`
    # command; you can skip calling this if have other means of specifying the contact name and output format
    cli_args = ica.get_cli_args()
    # Retrieve the dataframes corresponding to the massaged contents of the database; dataframes include `message` and `attachment`
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone
    )
    # Send the results to stdout in the given format
    ica.output_results(
        pd.DataFrame(
            {
                "timestamp": dfs.messages["datetime"],
                "is_from_me": dfs.messages["is_from_me"],
                "is_reaction": dfs.messages["is_reaction"],
                # U+FFFC is the object replacement character, which appears as
                # the textual message for every attachment
                "message": dfs.messages["text"].replace(
                    r"\ufffc", "(attachment)", regex=True
                ),
            }
        ),
        # The default format (None) is the pandas default dataframe table format
        format=cli_args.format,
    )


if __name__ == "__main__":
    main()
```

You can run the above program using the `ica` command, or execute it directly
like any other Python program.

```sh
ica ./get_my_transcript.py -c 'John Doe'
```

```sh
python ./get_my_transcript.py -c 'John Doe'
```

```sh
python -m get_my_transcript -c 'John Doe'
```

You're not limited to writing a command line program, though! The
`ica.get_dataframes()` function is the only function you will need in any
analyzer program. But beyond that, feel free to import other modules, send your
results to other processes, or whatever you need to do!

#### A note about timezones

By default, all dates and times are in the local timezone of the system on which
ICA is run. If you'd like to change this, you can pass the `--timezone` / `-t`
option to the CLI with an IANA timezone name.

```sh
ica message_totals -c 'John Doe' -t UTC
```

```sh
ica message_totals -c 'John Doe' -t America/New_York
```

The equivalent option for the Python API is the `timezone` parameter to
`ica.get_dataframes`:

```python
dfs = ica.get_dataframes(contact_name=my_contact_name, timezone='UTC')
```
