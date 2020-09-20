# iMessage Conversation Analyzer

*Copyright 2020 Caleb Evans*  
*Released under the MIT license*

## Credits

[Blog post by Yorgos Askalidis][blog-post]

[blog-post]: https://towardsdatascience.com/heres-how-you-can-access-your-entire-imessage-history-on-your-mac-f8878276c6e9

## Installation

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

## Usage

#### -p / --phone-number

Required; the phone number of the recipient whose conversation you want to fetch
(between you and the recipient). The phone number must be digits only; no spaces
or leading `+`.

#### -m / --metric-file

Required; a Python file with an `analyze()` function; this file must return a
pandas `DataFrame`. See the examples in `ica/metrics`.

### -f / --format

Optional; the output format of the result. Omit this argument for a simple
textual table, or specify `csv` to print output as CSV.

```sh
ica -p 1234567890 -m ica/metrics/message_totals.py -f csv
```
