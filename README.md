# iMessage Conversation Analyzer

*Copyright 2020-2024 Caleb Evans*  
*Released under the MIT license*

[![tests](https://github.com/caleb531/imessage-conversation-analyzer/actions/workflows/tests.yml/badge.svg)](https://github.com/caleb531/imessage-conversation-analyzer/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/caleb531/imessage-conversation-analyzer/badge.svg?branch=main)](https://coveralls.io/r/caleb531/imessage-conversation-analyzer?branch=main)

iMessage Conversation Analyzer (ICA) is a fully-typed Python library that will
read the contents of an iMessage conversation via the Messages app's database on
macOS. You can then gather various metrics of interest on the messages. The library also includes a CLI utility for easy use.

Much of this program was inspired by and built using findings from [this blog post by Yorgos Askalidis][blog-post].

[blog-post]: https://towardsdatascience.com/heres-how-you-can-access-your-entire-imessage-history-on-your-mac-f8878276c6e9

### Caveats

- Group chats (three or more people) are not supported at this time
- This program only runs on macOS

## Installation

Open a Terminal and run the following:

```sh
pip3 install imessage-conversation-analyzer
```

## Usage

The package includes both a Command Line API for simplicity/convenience, as well
as a Python API for developers who want maximum flexibility.

### Command Line API

To use ICA from the command line, run the `ica` command from the Terminal. The
minimum required arguments are:

1. A path to an analyzer file to run, or the name of a built-in analyzer
2. The first and last name of the contact, via the `-c`/`--contact` flag
   1. If the contact has no last name on record, you can just pass the first
      name

#### Example

```sh
ica message_totals -c 'Jane Fernbrook'
```

The following outputs a table like:

```
Metric               Total
Messages             14535
Messages From Me      7289
Messages From Them    7246
Reactions             5050
Reactions From Me     3901
Reactions From Them   1149
Days Messaged          115
Days Missed              0
Days With No Reply       0
```

#### Built-in analyzers

ICA includes several built-in analyzers out of the box:

1. `message_totals`: a summary of message and reaction counts, by person and in
   total, as well as other insightful metrics
2. `attachment_totals`: lists count data by attachment type, including
   number of Spotify links shared, YouTube videos, Apple Music, etc.
3. `most_frequent_emojis`: count data for the top 10 most frequently used emojis
   across the entire conversation
4. `totals_by_day`: a comprehensive breakdown of message totals for every day
   you and the other person have been messaging in the conversation
5. `transcript`: a full, unedited transcript of every message, including
   reactions, between you and the other person (attachment files not included)

##### Example

```sh
ica most_frequent_emojis -c 'Jane Fernbrook'
```

### Other formats

You can optionally pass the `-f`/`--format` flag to output to a specific format
like CSV (supported formats include `csv`, `excel`/`xlsx`, and `markdown`/`md`).

```sh
ica message_totals -c 'Jane Fernbrook' -f csv
```

```sh
ica ./my_custom_analyzer.py -c 'Jane Fernbrook' -f csv
```

### Writing to a file

Finally, there is an optional `-o`/`--output` flag if you want to output to a
specified file. ICA will do its best to infer the format from the file
extension, although you could also pass `--format` if you have special filename
requirements.

```sh
ica transcript -c 'Thomas Riverstone' -o ./my_transcript.xlsx
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
    # command; you can skip calling this if have other means of specifying the
    # contact name and output format
    cli_args = ica.get_cli_args()
    # Retrieve the dataframes corresponding to the massaged contents of the
    # database; dataframes include `message` and `attachment`
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone
    )
    # Send the results to stdout (or to file) in the given format
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
        # The default format (None) corresponds to the pandas default dataframe
        # table format
        format=cli_args.format,
        # When output is None (the default), ICA will print to stdout
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
```

You can run the above program using the `ica` command, or execute it directly
like any other Python program.

```sh
ica ./get_my_transcript.py -c 'Thomas Riverstone'
```

```sh
python ./get_my_transcript.py -c 'Thomas Riverstone'
```

```sh
python -m get_my_transcript -c 'Thomas Riverstone'
```

You're not limited to writing a command line program, though! The
`ica.get_dataframes()` function is the only function you will need in any
analyzer program. But beyond that, feel free to import other modules, send your
results to other processes, or whatever you need to do!

You can also import any built-in analyzer (for your own post-processing) via the
`ica.analyzers` namespace.

### Errors and exceptions

- `BaseAnalyzerException`: the base exception class for all library-related
  errors and exceptions
- `ContactNotFoundError`: raised if the specified contact was not found
- `ConversationNotFoundError`: raised if the specified conversation was not
  found
- `FormatNotSupportedError`: raised if the specified format is not supported by
  the library

#### Using a specific timezone

By default, all dates and times are in the local timezone of the system on which
ICA is run. If you'd like to change this, you can pass the `--timezone` / `-t`
option to the CLI with an IANA timezone name.

```sh
ica totals_by_day -c 'Daniel Brightingale' -t UTC
```

```sh
ica totals_by_day -c 'Daniel Brightingale' -t America/New_York
```

The equivalent option for the Python API is the `timezone` parameter to
`ica.get_dataframes`:

```python
dfs = ica.get_dataframes(contact_name=my_contact_name, timezone='UTC')
```

## Developer Setup

The following instructions are written for developers who want to run the
package locally, or write their own analyzers.

### 1. Set up virtualenv

```sh
pip3 install virtualenv
```

```sh
virtualenv --python=python3 .virtualenv
source .virtualenv/bin/activate
```

### 2. Install project depdendencies

```sh
pip install -r requirements.txt
```
