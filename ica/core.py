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
import tzlocal
from tabulate import tabulate
from typedstream.stream import TypedStreamReader

import ica.contact as contact
from ica.exceptions import ConversationNotFoundError

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
    connection: sqlite3.Connection,
    chat_identifiers: list[str],
    timezone: Union[str, None] = None,
) -> pd.DataFrame:
    # If no IANA timezone name is specified, default to the name of the system's
    # local timezone
    if not timezone:
        timezone = tzlocal.get_localzone().key
    return (
        pd.read_sql_query(
            sql=importlib.resources.files(__package__)
            .joinpath(os.path.join("queries", "messages.sql"))
            .read_text(),
            con=connection,
            params={
                "chat_identifiers": get_chat_identifier_str(chat_identifiers),
                "chat_identifier_delimiter": CHAT_IDENTIFIER_DELIMITER,
            },
            parse_dates={"datetime": "ISO8601"},
        )
        # SQL provides each date/time as a Unix timestamp (which is implicitly
        # UTC), but the timestamp is timezone-naive when parsed by pandas; so
        # first, we must add the missing timezone information, then we must
        # convert the datetime to the specified timezone
        .assign(
            datetime=lambda df: df["datetime"]
            .dt.tz_localize("UTC")
            .dt.tz_convert(timezone)
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
    connection: sqlite3.Connection,
    chat_identifiers: list[str],
    timezone: Union[str, None] = None,
) -> pd.DataFrame:
    return pd.read_sql_query(
        sql=importlib.resources.files(__package__)
        .joinpath(os.path.join("queries", "attachments.sql"))
        .read_text(),
        con=connection,
        params={
            "chat_identifiers": get_chat_identifier_str(chat_identifiers),
            "chat_identifier_delimiter": CHAT_IDENTIFIER_DELIMITER,
        },
    )


# Return all dataframes for a specific macOS Messages conversation
def get_dataframes(
    contact_name: str, timezone: Union[str, None] = None
) -> DataFrameNamespace:
    chat_identifiers = contact.get_chat_identifiers(contact_name)

    with sqlite3.connect(DB_PATH) as connection:
        dfs = DataFrameNamespace(
            messages=get_messages_dataframe(connection, chat_identifiers, timezone),
            attachments=get_attachments_dataframe(
                connection, chat_identifiers, timezone
            ),
        )
        if dfs.messages.empty:
            raise ConversationNotFoundError(
                f'No conversation was found for the contact "{contact_name}"'
            )
        return dfs


# Format the given header name to be more human-readable (e.g. "foo_bar" =>
# "Foo Bar")
def prettify_header_name(header_name: Union[str, int]) -> Union[str, int]:
    if header_name and type(header_name) is str:
        return header_name.replace("_", " ").title()
    else:
        return header_name


# Print the given dataframe of metrics data
def output_results(
    analyzer_df: pd.DataFrame, format: Union[str, None] = "default"
) -> None:
    is_default_index = not analyzer_df.index.name
    output_df = (
        analyzer_df.rename(
            # Prettify header column (i.e. textual values in first column)
            index=prettify_header_name,
            # Prettify header row (i.e. column names)
            columns={
                column_name: prettify_header_name(column_name)
                for column_name in analyzer_df.columns
            },
        )
        # Prettify index column name
        .rename_axis(prettify_header_name(analyzer_df.index.name), axis=0)
        # Make all indices start from 1 instead of 0, but only if the index is
        # the default (rather than a custom column)
        .pipe(lambda df: df.set_index(df.index + 1 if not df.index.name else df.index))
    )

    # Output executed DataFrame to correct format
    if format == "csv":
        print(output_df.to_csv(index=not is_default_index, header=output_df.columns))
    else:
        print(
            tabulate(
                output_df,
                # pandas treats the index name separately from the other column
                # names, whereas tabulate represents all header row names as a
                # single list; therefore, we must include the index name if this
                # list if the index has a name
                headers=([output_df.index.name] if output_df.index.name else [])
                + list(output_df.columns),
            )
        )
