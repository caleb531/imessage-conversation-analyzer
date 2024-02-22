#!/usr/bin/env python3

import importlib.machinery
import importlib.resources
import importlib.util
import os
import os.path
import sqlite3
import sys
from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path
from typing import Callable, Union

import pandas as pd
import tzlocal
from typedstream.stream import TypedStreamReader

import ica.contact as contact
from ica.exceptions import ConversationNotFoundError, FormatNotSupportedError

# In order to interpolate the user-specified list of chat identifiers into the
# SQL queries, we must join the list into a string delimited by a common
# symbol, then perform a LIKE comparison on this string within the SQL query;
# this is because named SQL parameters only support string values, rather than
# variable-length sequences
CHAT_IDENTIFIER_DELIMITER = "|"


# The path to the database file for the macOS Messages application
DB_PATH = os.path.expanduser(os.path.join("~", "Library", "Messages", "chat.db"))


# The formats supported for file output, represented as a dictionary where each
# key is the format name and the value is the file extension corresponding to
# that format
SUPPORTED_OUTPUT_FORMAT_MAP = {"csv": "csv", "excel": "xlsx", "markdown": "md"}


@dataclass
class DataFrameNamespace:
    """
    The namespace containing the relevant dataframes for the specified user in
    the chat database
    """

    messages: pd.DataFrame
    attachments: pd.DataFrame


def get_chat_identifier_str(chat_identifiers: list[str]) -> str:
    """
    Join the list of chat identifiers into a delimited string; in order for the
    SQL comparison to function properly, this string must also start and end
    with the delimiter symbol
    """
    return "{start}{joined}{end}".format(
        start=CHAT_IDENTIFIER_DELIMITER,
        joined=CHAT_IDENTIFIER_DELIMITER.join(chat_identifiers),
        end=CHAT_IDENTIFIER_DELIMITER,
    )


def decode_message_attributedbody(data: bytes) -> str:
    """
    The textual contents of some messages are encoded in a special
    attributedBody column on the message row; this attributedBody value is
    in Apple's proprietary typedstream format, but can be parsed with the
    pytypedstream package (<https://pypi.org/project/pytypedstream/>)
    """
    if data:
        for event in TypedStreamReader.from_data(data):
            # The first bytes object is the one we want; it should be safe to
            # convert back to UTF-8
            if type(event) is bytes:
                return event.decode("utf-8")
    return ""


def pipe_lambda(
    df_lambda: Callable[[pd.DataFrame], pd.DataFrame]
) -> Callable[[pd.DataFrame], pd.DataFrame]:
    """
    If you pass a lambda to the DataFrame pipe() method, the type of the
    dataframe parameter and the return type of the lambda will both be `Any`;
    this breaks type-safety for the lambda itself and for subsequent chained
    methods, but to work around this, we can introduce a wrapper function which,
    when wrapped around the lambda, can enforce the proper type within mypy
    """
    return df_lambda


def assign_lambda(
    df_lambda: Callable[[pd.DataFrame], pd.Series]
) -> Callable[[pd.DataFrame], pd.Series]:
    """
    If you pass a lambda to the DataFrame assign() method, the type of the
    dataframe parameter and the return type of the lambda will both be `Any`;
    this breaks type-safety for the lambda itself and for subsequent chained
    methods, but to work around this, we can introduce a wrapper function which,
    when wrapped around the lambda, can enforce the proper type within mypy
    """
    return df_lambda


def get_messages_dataframe(
    connection: sqlite3.Connection,
    chat_identifiers: list[str],
    timezone: Union[str, None] = None,
) -> pd.DataFrame:
    """
    Return a pandas dataframe representing all messages in a particular
    conversation (identified by the given phone number)
    """
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
            datetime=assign_lambda(
                lambda df: df["datetime"].dt.tz_localize("UTC").dt.tz_convert(timezone)
            )
        )
        # Decode any 'attributedBody' values and merge them into the 'text'
        # column
        .assign(
            text=assign_lambda(
                lambda df: df["text"].fillna(
                    df["attributedBody"].apply(decode_message_attributedbody)
                )
            )
        )
        # Remove 'attributedBody' column now that it has been merged into the
        # 'text' column
        .drop("attributedBody", axis="columns")
        # Use a regex-based heuristic to determine which messages are reactions
        .assign(
            is_reaction=assign_lambda(
                lambda df: df["text"].str.match(
                    r"^(Loved|Liked|Disliked|Laughed at|Emphasized|Questioned)"
                    r" (“(.*?)”|an \w+)$"
                )
            )
        )
        # Convert 'is_from_me' values from integers to proper booleans
        .assign(is_from_me=assign_lambda(lambda df: df["is_from_me"].astype(bool)))
    )


def get_attachments_dataframe(
    connection: sqlite3.Connection,
    chat_identifiers: list[str],
    timezone: Union[str, None] = None,
) -> pd.DataFrame:
    """
    Return a pandas dataframe representing all attachments in a particular
    conversation (identified by the given phone number)
    """
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


def get_dataframes(
    contact_name: str, timezone: Union[str, None] = None
) -> DataFrameNamespace:
    """
    Return all dataframes for a specific macOS Messages conversation
    """
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
                f'No conversation found for the contact "{contact_name}"'
            )
        return dfs


def prettify_header_name(header_name: Union[str, int]) -> Union[str, int]:
    """
    Format the given header name to be more human-readable (e.g. "foo_bar" =>
    "Foo Bar")
    """
    if header_name and type(header_name) is str:
        return header_name.replace("_", " ").title()
    else:
        return header_name


def infer_format_from_output_file_path(output: Union[str, None]) -> Union[str, None]:
    """
    Assuming an explicit format was not provided, infer the format from the
    extension of the given output file path
    """
    if not output:
        return None
    ext = Path(output).suffix[1:]
    if ext not in SUPPORTED_OUTPUT_FORMAT_MAP.values():
        return None
    return ext


def make_dataframe_tz_naive(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all of the datetime timstamps in the given dataframe to be
    timezone-naive, including all columns and the index
    """
    return df.pipe(
        pipe_lambda(
            lambda df: (
                df.set_index(df.index.tz_localize(None))
                if isinstance(df.index, pd.DatetimeIndex)
                else df
            )
        )
    ).assign(
        **{
            col: df[col].dt.tz_localize(None)
            for col in df.select_dtypes(include=["datetime64[ns, UTC]"])
        }
    )


def prepare_df_for_output(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the given dataframe for output by prettifying column names,
    strippnig timezone details incompatible with Excel, and other normalization
    operations; return the normalized dataframe
    """
    return (
        df.rename(
            # Prettify header column (i.e. textual values in first column)
            index=prettify_header_name,
            # Prettify header row (i.e. column names)
            columns=prettify_header_name,
        )
        # Prettify index column name
        .rename_axis(prettify_header_name(df.index.name), axis="index")
        # Make all indices start from 1 instead of 0, but only if the index is
        # the default (rather than a custom column)
        .pipe(
            pipe_lambda(
                lambda df: df.set_index(df.index + 1 if not df.index.name else df.index)
            )
        )
        # Make dataframe timestamps timezone-naive (which is required for
        # exporting to Excel)
        .pipe(pipe_lambda(lambda df: make_dataframe_tz_naive(df)))
    )


def output_results(
    analyzer_df: pd.DataFrame,
    format: Union[str, None] = None,
    output: Union[str, None, StringIO, BytesIO] = None,
) -> None:
    """
    Print the dataframe provided by an analyzer module
    """
    is_default_index = not analyzer_df.index.name
    output_df = prepare_df_for_output(analyzer_df)

    if format and format not in {
        *SUPPORTED_OUTPUT_FORMAT_MAP.keys(),
        *SUPPORTED_OUTPUT_FORMAT_MAP.values(),
    }:
        raise FormatNotSupportedError(
            f'The format "{format}" is not supported for output'
        )

    if not format and type(output) is str:
        format = infer_format_from_output_file_path(output)

    output_not_specified: bool = False
    if not output and format in ("excel", "xlsx"):
        output_not_specified = True
        output = BytesIO()
    elif not output:
        output_not_specified = True
        output = StringIO()

    # Keyword arguments passed to any of the to_* output methods
    output_args: dict = {"index": not is_default_index}

    # Output executed DataFrame to correct format
    if format in ("xlsx", "excel"):
        output_df.to_excel(output, **output_args)
    elif format == "csv":
        output_df.to_csv(output, **output_args)
    elif format in ("md", "markdown"):
        output_df.to_markdown(output, **output_args)
    else:
        (
            output_df
            # When we output the dataframe with to_string(), if the index has a
            # name, it will be displayed on a separate line underneath the line
            # with the column names; this is because space needs to be reserved
            # for the columns axis name; to solve this, we can make the name of
            # the index the name of the columns axis, then remove the name from
            # the index (source: <https://stackoverflow.com/a/43635736/560642>)
            .rename_axis(output_df.index.name, axis="columns")
            .rename_axis(None, axis="index")
            .to_string(output, index=True, line_width=100000)
        )

    # Print output if no output file path was supplied
    if output_not_specified and type(output) is BytesIO:
        sys.stdout.buffer.write(output.getvalue())
    elif output_not_specified and type(output) is StringIO:
        print(output.getvalue(), flush=True)
