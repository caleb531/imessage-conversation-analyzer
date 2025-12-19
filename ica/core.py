#!/usr/bin/env python3

import csv
import importlib.resources
import os
import sys
from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Hashable, Optional, Union

import duckdb
import duckdb.sqltypes
import openpyxl
import tabulate
import tzlocal
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
class ConversationData:
    """
    The namespace containing the relevant DuckDB relations for the specified user
    in the chat database
    """

    con: duckdb.DuckDBPyConnection
    messages: duckdb.DuckDBPyRelation
    attachments: duckdb.DuckDBPyRelation


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
                return event.decode("utf-8", errors="replace")
    return ""


def get_messages_relation(
    con: duckdb.DuckDBPyConnection,
    chat_identifiers: list[str],
    timezone: Optional[str] = None,
) -> duckdb.DuckDBPyRelation:
    """
    Return a DuckDB relation representing all messages in a particular
    conversation (identified by the given phone number or email address)
    """
    # If no IANA timezone name is specified, default to the name of the system's
    # local timezone
    if not timezone:
        timezone = tzlocal.get_localzone().key

    query = (
        importlib.resources.files("ica")
        .joinpath(os.path.join("queries", "messages.sql"))
        .read_text()
    )

    # We need to pass the chat identifiers string to the query
    chat_identifiers_str = get_chat_identifier_str(chat_identifiers)

    rel = con.sql(query, params=[chat_identifiers_str])

    # Apply transformations that were previously done in Pandas
    # 1. Timezone conversion
    # 2. Reaction detection
    # 3. Boolean conversion for is_from_me

    # Note: The SQL query already handles COALESCE(text, decode_body(attributedBody))

    return rel.project(
        f"""
        ROWID,
        text,
            timezone('{timezone}',
                to_timestamp(CAST(date AS BIGINT) / 1000000000 + 978307200)
            ) as datetime,
        CASE WHEN regexp_matches(text,
            '^(Loved|Liked|Disliked|Laughed at|Emphasized|Questioned|Reacted) ' ||
            '(“(.*?)”|an \\w+|(.*?) to “(.*?)”)$'
        ) THEN true ELSE NULL END as is_reaction,
        CAST(is_from_me AS BOOLEAN) as is_from_me
        """
    )


def filter_relation(
    rel: duckdb.DuckDBPyRelation,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    from_person: Optional[str] = None,
) -> duckdb.DuckDBPyRelation:
    """
    Return a copy of the messages relation that has been filtered by the
    user-supplied filters
    """
    # Raise an exception if the 'from' date is after the 'to' date
    # We can't easily check this without parsing dates, but we can trust the
    # user or check strings
    if from_date and to_date and from_date > to_date:
        raise DateRangeInvalidError("Date range is backwards")

    if from_person == "me":
        rel = rel.filter("is_from_me = true")
    elif from_person == "them":
        rel = rel.filter("is_from_me = false")

    if from_date:
        rel = rel.filter(f"datetime >= '{from_date}'")

    if to_date:
        rel = rel.filter(f"datetime <= '{to_date}'")

    return rel


def get_attachments_relation(
    con: duckdb.DuckDBPyConnection,
    chat_identifiers: list[str],
    timezone: Optional[str] = None,
) -> duckdb.DuckDBPyRelation:
    """
    Return a DuckDB relation representing all attachments in a particular
    conversation (identified by the given phone number)
    """
    if not timezone:
        timezone = tzlocal.get_localzone().key

    query = (
        importlib.resources.files("ica")
        .joinpath(os.path.join("queries", "attachments.sql"))
        .read_text()
    )

    chat_identifiers_str = get_chat_identifier_str(chat_identifiers)
    rel = con.sql(query, params=[chat_identifiers_str])

    return rel.project(
        f"""
        ROWID,
        mime_type,
        filename,
        message_id,
            timezone('{timezone}',
                to_timestamp(CAST(date AS BIGINT) / 1000000000 + 978307200)
            ) as datetime,
        CAST(is_from_me AS BOOLEAN) as is_from_me
        """
    )


def get_conversation_data(
    contact_name: str,
    timezone: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    from_person: Optional[str] = None,
) -> ConversationData:
    """
    Return all relations for a specific macOS Messages conversation
    """
    chat_identifiers = contact.get_chat_identifiers(contact_name)

    con = duckdb.connect(":memory:")
    # Attach the SQLite database
    # We use read_only=True to ensure we don't modify the chat.db
    con.execute(f"ATTACH '{DB_PATH}' AS chat_db (TYPE SQLITE, READ_ONLY TRUE)")
    con.execute("USE chat_db")

    # Register the UDF for decoding attributedBody
    con.create_function(
        "decode_body",
        decode_message_attributedbody,
        [duckdb.sqltypes.BLOB],
        duckdb.sqltypes.VARCHAR,
    )

    messages = get_messages_relation(con, chat_identifiers, timezone)
    attachments = get_attachments_relation(con, chat_identifiers, timezone)

    # Materialize the relations into in-memory DuckDB tables to avoid re-running
    # the expensive Python UDF and Regex for every subsequent query
    con.sql("CREATE TEMPORARY TABLE messages_base AS SELECT * FROM messages")
    messages = con.table("messages_base")

    con.sql("CREATE TEMPORARY TABLE attachments_base AS SELECT * FROM attachments")
    attachments = con.table("attachments_base")

    # Check if conversation exists (efficiently)
    res = messages.count("ROWID").fetchone()
    count = res[0] if res else 0
    if count == 0:
        con.close()
        raise ConversationNotFoundError(
            f'No conversation found for the contact "{contact_name}"'
        )

    messages = filter_relation(messages, from_date, to_date, from_person)
    attachments = filter_relation(attachments, from_date, to_date, from_person)

    return ConversationData(con, messages, attachments)


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


def output_results(
    data: Union[duckdb.DuckDBPyRelation, list[dict[str, Any]]],
    format: Optional[str] = None,
    output: Union[str, StringIO, BytesIO, None] = None,
    prettify_index: bool = True,
) -> None:
    """
    Print the results provided by an analyzer module
    """
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

    # Convert data to list of dicts if it's a relation
    if isinstance(data, duckdb.DuckDBPyRelation):
        # Fetch all data
        columns = data.columns
        rows = data.fetchall()
        # Convert to list of dicts for easier handling
        # Note: This loads data into memory, but it's the result set, which is
        # usually smaller
        data_list = [dict(zip(columns, row)) for row in rows]
    else:
        data_list = data
        if not data_list:
            columns = []
        else:
            columns = list(data_list[0].keys())

    # Prettify headers
    headers = [prettify_header_name(c) for c in columns]

    # Output to correct format
    if format in ("xlsx", "excel"):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(headers)
        for row in data_list:
            ws.append(list(row.values()))

        if isinstance(output, BytesIO):
            wb.save(output)
        elif isinstance(output, str):
            wb.save(output)

    elif format == "csv":
        if isinstance(output, str):
            with open(output, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in data_list:
                    writer.writerow(list(row.values()))
        else:
            # output is StringIO here because we set it up that way for
            # non-excel formats if it wasn't specified, or it's a file object
            # passed in. However, type checker doesn't know that output isn't
            # BytesIO here.
            if isinstance(output, BytesIO):
                raise ValueError("Cannot write CSV to BytesIO")
            writer = csv.writer(output)
            writer.writerow(headers)
            for row in data_list:
                writer.writerow(list(row.values()))

    elif format in ("md", "markdown"):
        table = [list(row.values()) for row in data_list]
        content = tabulate.tabulate(table, headers=headers, tablefmt="github")
        if isinstance(output, str):
            with open(output, "w") as f:
                f.write(content)
        else:
            output.write(content)

    else:
        # Default text output
        table = [list(row.values()) for row in data_list]
        content = tabulate.tabulate(table, headers=headers, tablefmt="plain")
        if isinstance(output, str):
            with open(output, "w") as f:
                f.write(content)
        else:
            output.write(content)

    # Print output if no output file path was supplied
    if output_not_specified and isinstance(output, BytesIO):
        sys.stdout.buffer.write(output.getvalue())
    elif output_not_specified and isinstance(output, StringIO):
        print(output.getvalue(), flush=True)


def get_sql_connection(
    data: ConversationData,
) -> duckdb.DuckDBPyConnection:
    """
    Return the existing DuckDB connection.
    """
    return data.con


def execute_sql_query(
    query: str, con: duckdb.DuckDBPyConnection
) -> duckdb.DuckDBPyRelation:
    """
    Execute the given arbitrary SQL query
    """
    return con.sql(query)
