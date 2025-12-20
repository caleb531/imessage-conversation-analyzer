#!/usr/bin/env python3

import importlib.machinery
import importlib.resources
import importlib.util
import os
import sqlite3
import sys
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import Hashable, Optional, Union

import duckdb
import polars as pl
import tzlocal
from tabulate import tabulate
from typedstream.stream import TypedStreamReader

import ica.contact as contact
from ica.exceptions import (
    ConversationNotFoundError,
    DateRangeInvalidError,
    FormatNotSupportedError,
)

# In order to interpolate the user-specified list of chat identifiers into the
# SQL queries, we must join the list into a string delimited by a common
# symbol, then perform a LIKE comparison on this string within the SQL query;
# this is because named SQL parameters only support string values, rather than
# variable-length sequences
CHAT_IDENTIFIER_DELIMITER = "|"


# The path to the database file for the macOS Messages application
DB_PATH = Path.home() / "Library" / "Messages" / "chat.db"


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

    messages: pl.DataFrame
    attachments: pl.DataFrame


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


def get_messages_dataframe(
    con: sqlite3.Connection,
    chat_identifiers: list[str],
    timezone: Optional[str] = None,
) -> pl.DataFrame:
    """
    Return a polars dataframe representing all messages in a particular
    conversation (identified by the given phone number or email address)
    """
    # If no IANA timezone name is specified, default to the name of the system's
    # local timezone
    if not timezone:
        timezone = tzlocal.get_localzone().key

    query_template = (
        importlib.resources.files("ica")
        .joinpath(os.path.join("queries", "messages.sql"))
        .read_text()
    )
    # Manually interpolate parameters since pl.read_database doesn't support
    # parameterized queries for sqlite3 connections
    query = query_template.replace(
        ":chat_identifiers", f"'{get_chat_identifier_str(chat_identifiers)}'"
    ).replace(":chat_identifier_delimiter", f"'{CHAT_IDENTIFIER_DELIMITER}'")

    df = (
        pl.read_database(query=query, connection=con)
        # SQL provides each date/time as a Unix timestamp (which is implicitly
        # UTC), but the timestamp is timezone-naive when parsed; so first, we
        # must add the missing timezone information, then we must convert the
        # datetime to the specified timezone
        .with_columns(
            pl.col("datetime")
            .str.to_datetime()
            .dt.replace_time_zone("UTC")
            .dt.convert_time_zone(timezone)
        )
    )

    # Decode any 'attributedBody' values and merge them into the 'text' column
    # Optimization: Only run the expensive decoding on rows where 'text' is null
    # and 'attributedBody' is present
    df_text_ok = df.filter(pl.col("text").is_not_null())
    df_text_null = df.filter(pl.col("text").is_null())

    if not df_text_null.is_empty():
        df_text_null = df_text_null.with_columns(
            pl.col("attributedBody")
            .map_elements(decode_message_attributedbody, return_dtype=pl.Utf8)
            .alias("text")
        )

    return (
        pl.concat([df_text_ok, df_text_null])
        # Remove 'attributedBody' column now that it has been merged into the
        # 'text' column
        .drop("attributedBody")
        # Use a regex-based heuristic to determine which messages are reactions
        .with_columns(
            is_reaction=pl.col("text").str.contains(
                r"^(Loved|Liked|Disliked|Laughed at|Emphasized|Questioned|Reacted)"
                r" (“(.*?)”|an \w+|(.*?) to “(.*?)”)$"
            )
        )
        # Convert 'is_from_me' values from integers to proper booleans
        .with_columns(is_from_me=pl.col("is_from_me").cast(pl.Boolean))
    )


def filter_dataframe(
    df: pl.DataFrame,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    from_person: Optional[str] = None,
) -> pl.DataFrame:
    """
    Return a copy of the messages dataframe that has been filtered by the
    user-supplied filters
    """

    # Raise an exception if the 'from' date is after the 'to' date
    if (
        from_date
        and to_date
        and datetime.fromisoformat(from_date) > datetime.fromisoformat(to_date)
    ):
        raise DateRangeInvalidError("Date range is backwards")

    if from_person == "me":
        df = df.filter(pl.col("is_from_me"))
    elif from_person == "them":
        df = df.filter(~pl.col("is_from_me"))

    if from_date:
        df = df.filter(pl.col("datetime") >= pl.lit(from_date).str.to_datetime())
    if to_date:
        df = df.filter(pl.col("datetime") <= pl.lit(to_date).str.to_datetime())

    return df


def get_attachments_dataframe(
    con: sqlite3.Connection,
    chat_identifiers: list[str],
    timezone: Optional[str] = None,
) -> pl.DataFrame:
    """
    Return a polars dataframe representing all attachments in a particular
    conversation (identified by the given phone number)
    """
    query_template = (
        importlib.resources.files("ica")
        .joinpath(os.path.join("queries", "attachments.sql"))
        .read_text()
    )
    query = query_template.replace(
        ":chat_identifiers", f"'{get_chat_identifier_str(chat_identifiers)}'"
    ).replace(":chat_identifier_delimiter", f"'{CHAT_IDENTIFIER_DELIMITER}'")

    return (
        pl.read_database(query=query, connection=con)
        # Expose the date/time of the message alongside each attachment record,
        # for convenience
        .with_columns(
            pl.col("datetime")
            .str.to_datetime()
            .dt.replace_time_zone("UTC")
            .dt.convert_time_zone(timezone)
        )
    )


def get_dataframes(
    contact_name: str,
    timezone: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    from_person: Optional[str] = None,
) -> DataFrameNamespace:
    """
    Return all dataframes for a specific macOS Messages conversation
    """
    chat_identifiers = contact.get_chat_identifiers(contact_name)
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as con:
        dfs = DataFrameNamespace(
            messages=get_messages_dataframe(con, chat_identifiers, timezone),
            attachments=get_attachments_dataframe(con, chat_identifiers, timezone),
        )
        if dfs.messages.is_empty():
            raise ConversationNotFoundError(
                f'No conversation found for the contact "{contact_name}"'
            )
        dfs.messages = filter_dataframe(
            dfs.messages,
            from_date,
            to_date,
            from_person,
        )
        dfs.attachments = filter_dataframe(
            dfs.attachments,
            from_date,
            to_date,
            from_person,
        )
        return dfs


def prettify_header_name(header_name: Hashable) -> Hashable:
    """
    Format the given header name to be more human-readable (e.g. "foo_bar" =>
    "Foo Bar")
    """
    if header_name and type(header_name) is str:
        return header_name.replace("_", " ").title()
    else:
        return header_name


def infer_format_from_output_file_path(output: Optional[str]) -> Optional[str]:
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


def make_dataframe_tz_naive(df: pl.DataFrame) -> pl.DataFrame:
    """
    Convert all of the datetime timstamps in the given dataframe to be
    timezone-naive, including all columns
    """
    return df.with_columns(
        pl.col(col).dt.replace_time_zone(None)
        for col, dtype in zip(df.columns, df.dtypes)
        if isinstance(dtype, pl.Datetime) and dtype.time_zone is not None
    )


def prepare_df_for_output(
    df: pl.DataFrame, prettify_index: bool = True
) -> pl.DataFrame:
    """
    Prepare the given dataframe for output by prettifying column names,
    stripping timezone details incompatible with Excel, and other normalization
    operations; return the normalized dataframe
    """
    return (
        df.rename(
            # Prettify header row (i.e. column names)
            {col: prettify_header_name(col) for col in df.columns}
        )
        # Make dataframe timestamps timezone-naive (which is required for
        # exporting to Excel)
        .pipe(make_dataframe_tz_naive)
    )


def output_results(
    analyzer_df: pl.DataFrame,
    format: Optional[str] = None,
    output: Union[str, StringIO, BytesIO, None] = None,
    prettify_index: bool = True,
) -> None:
    """
    Print the dataframe provided by an analyzer module
    """
    output_df = prepare_df_for_output(analyzer_df, prettify_index=prettify_index)

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

    # Output executed DataFrame to correct format
    if format in ("xlsx", "excel"):
        output_df.write_excel(output)
    elif format == "csv":
        output_df.write_csv(output)
    elif format in ("md", "markdown"):
        # Polars doesn't have to_markdown, so we use tabulate
        if isinstance(output, (StringIO, BytesIO)):
            output.write(
                tabulate(output_df.to_dicts(), headers="keys", tablefmt="github")
            )
        else:
            with open(output, "w") as f:
                f.write(
                    tabulate(output_df.to_dicts(), headers="keys", tablefmt="github")
                )
    else:
        # Default output
        if isinstance(output, (StringIO, BytesIO)):
            output.write(str(output_df))
        else:
            with open(output, "w") as f:
                f.write(str(output_df))

    # Print output if no output file path was supplied
    if output_not_specified and type(output) is BytesIO:
        sys.stdout.buffer.write(output.getvalue())
    elif output_not_specified and type(output) is StringIO:
        print(output.getvalue(), flush=True)


@contextmanager
def get_sql_connection(
    dfs: DataFrameNamespace,
) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    Create an in-memory DuckDB database containing all ICA dataframes, and yield
    a connection to that database; using DuckDB over sqlite3 ensures that the
    data is exposed virtually rather than copied, improving performance for
    large conversations
    """
    with duckdb.connect(":memory:") as con:
        con.register("messages", dfs.messages)
        con.register("attachments", dfs.attachments)
        yield con


# Execute an arbitrary SQL query against the database of all ICA dataframes
def execute_sql_query(query: str, con: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    """
    Execute the given arbitrary SQL query, provided a connection to the
    in-memory DuckDB database created by ica.get_sql_connection()
    """
    return con.execute(query).pl()
