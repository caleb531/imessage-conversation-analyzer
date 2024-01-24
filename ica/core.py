#!/usr/bin/env python3

import importlib.machinery
import importlib.resources
import importlib.util
import os
import os.path
import sqlite3
from dataclasses import dataclass
from typing import Union

import pandas as pd
from tabulate import tabulate
from typedstream.stream import TypedStreamReader

import ica.contact as contact

# In order to interpolate the user-specified list of chat identifiers into the
# SQL queries, we must join the list into a string delimited by a common
# symbol, then perform a LIKE comparison on this string within the SQL query;
# this is because named SQL parameters only support string values, rather than
# variable-length sequences
CHAT_IDENTIFIER_DELIMITER = "|"


# The path to the database file for the macOS Messages application
DB_PATH = os.path.expanduser(os.path.join("~", "Library", "Messages", "chat.db"))


@dataclass
class DataFrameNamespace:
    messages: pd.DataFrame
    attachments: pd.DataFrame


# Join the list of chat identifiers into a delimited string; in order for the
# SQL comparison to function properly, this string must also start and end with
# the delimiter symbol
def get_chat_identifier_str(chat_identifiers: list[str]) -> str:
    return "{start}{joined}{end}".format(
        start=CHAT_IDENTIFIER_DELIMITER,
        joined=CHAT_IDENTIFIER_DELIMITER.join(chat_identifiers),
        end=CHAT_IDENTIFIER_DELIMITER,
    )


# The textual contents of some messages are encoded in a special attributedBody
# column on the message row; this attributedBody value is in Apple's proprietary
# typedstream format, but can be parsed with the pytypedstream package
# (<https://pypi.org/project/pytypedstream/>)
def decode_message_attributedbody(data: bytes) -> str:
    if data:
        for event in TypedStreamReader.from_data(data):
            # The first bytes object is the one we want; it should be safe to
            # convert back to UTF-8
            if type(event) is bytes:
                return event.decode("utf-8")
    return ""


# Return a pandas dataframe representing all messages in a particular
# conversation (identified by the given phone number)
def get_messages_dataframe(
    connection: sqlite3.Connection, chat_identifiers: list[str]
) -> pd.DataFrame:
    return (
        pd.read_sql_query(
            sql=importlib.resources.files(__package__)
            .joinpath("queries/messages.sql")
            .read_text(),
            con=connection,
            params={
                "chat_identifiers": get_chat_identifier_str(chat_identifiers),
                "chat_identifier_delimiter": CHAT_IDENTIFIER_DELIMITER,
            },
            parse_dates={"datetime": "ISO8601"},
        )
        # Decode any 'attributedBody' values and merge them into the 'text'
        # column
        .assign(
            text=lambda df: df["text"].fillna(
                df["attributedBody"].apply(decode_message_attributedbody)
            )
        )
        # Remove 'attributedBody' column now that it has been merged into the
        # 'text' column
        .drop("attributedBody", axis=1)
        # Use a regex-based heuristic to determine which messages are reactions
        .assign(
            is_reaction=lambda df: df["text"].str.match(
                r"^(Loved|Liked|Disliked|Laughed at|Emphasized|Questioned)"
                r" (“(.*?)”|an \w+)$"
            )
        )
        # Convert 'is_from_me' values from integers to proper booleans
        .assign(is_from_me=lambda df: df["is_from_me"].astype(bool))
    )


# Return a pandas dataframe representing all attachments in a particular
# conversation (identified by the given phone number)
def get_attachments_dataframe(
    connection: sqlite3.Connection, chat_identifiers: list[str]
) -> pd.DataFrame:
    return pd.read_sql_query(
        sql=importlib.resources.files(__package__)
        .joinpath("queries/attachments.sql")
        .read_text(),
        con=connection,
        params={
            "chat_identifiers": get_chat_identifier_str(chat_identifiers),
            "chat_identifier_delimiter": CHAT_IDENTIFIER_DELIMITER,
        },
    )


# Return all dataframes for a specific macOS Messages conversation
def get_dataframes(contact_name: str) -> DataFrameNamespace:
    chat_identifiers = contact.get_chat_identifiers(contact_name)

    with sqlite3.connect(DB_PATH) as connection:
        return DataFrameNamespace(
            messages=get_messages_dataframe(connection, chat_identifiers),
            attachments=get_attachments_dataframe(connection, chat_identifiers),
        )


# Format the given header name to be more human-readable (e.g. "foo_bar" =>
# "Foo Bar")
def prettify_header_name(header_name: Union[str, int]) -> Union[str, int]:
    if header_name and type(header_name) is str:
        return header_name.replace("_", " ").title()
    else:
        return header_name


# Print the given dataframe of metrics data
def output_results(analyzer_df: pd.DataFrame, format: str) -> None:
    analyzer_df = analyzer_df.rename(
        # Prettify header column (i.e. textual values in first column)
        index=prettify_header_name,
        # Prettify header row (i.e. column names)
        columns={
            column_name: prettify_header_name(column_name)
            for column_name in analyzer_df.columns
        },
    )

    # Prettify index column name
    analyzer_df.index.name = prettify_header_name(analyzer_df.index.name)

    # Make all indices start from 1 instead of 0, but only if the index is the
    # default (rather than a custom column)
    is_default_index = not analyzer_df.index.name
    if is_default_index:
        analyzer_df.index += 1

    # Output executed DataFrame to correct format
    if format == "csv":
        print(
            analyzer_df.to_csv(index=not is_default_index, header=analyzer_df.columns)
        )
    else:
        print(
            tabulate(
                analyzer_df,
                headers=([analyzer_df.index.name] if analyzer_df.index.name else [])
                + list(analyzer_df.columns),
            )
        )
