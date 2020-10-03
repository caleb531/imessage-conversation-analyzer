# iMessage Conversation Analyzer

*Copyright 2020 Caleb Evans*  
*Released under the MIT license*

This macOS CLI program will read the contents of an iMessage conversation via
the Messages app's database on your Mac. You can then gather various metrics of
interest on the messages and attachments collected.

Much of this program was inspired by and built using findings from [this blog post by Yorgos Askalidis][blog-post].

[blog-post]: https://towardsdatascience.com/heres-how-you-can-access-your-entire-imessage-history-on-your-mac-f8878276c6e9

### Caveats

Please note that currently, you can only query conversations between you and a
single other person (i.e. group chats are currently unsupported).

## Installation

### 1. Install Python 3

macOS is bundled with Python 2 out of the box. You can install Python 3 with the
[Homebrew][homebrew] package manager.

[homebrew]: https://brew.sh/

```sh
brew install python@3
```

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

#### -p / --phone-number

Required; the phone number of the recipient whose conversation you want to fetch
(between you and the recipient). The phone number must be digits only; no spaces
or leading `+`.

#### -m / --metric-file

Required; a Python file with an `analyze()` function; this file must return a
pandas `DataFrame`. See the examples in `ica/metrics`.

#### -f / --format

Optional; the output format of the result. Omit this argument for a simple
textual table, or specify `csv` to print output as CSV.

```sh
ica -p 1234567890 -m ica/metrics/message_totals.py
```

You can also output as CSV and use the `pbcopy` command for easy copy/pasting
into a spreadsheet program (like Excel or Numbers).

```sh
ica -p 1234567890 -m ica/metrics/message_totals.py -f csv | pbcopy
```
