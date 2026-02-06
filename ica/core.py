#!/usr/bin/env python3
import contextlib
import functools
import importlib.machinery
import importlib.resources
import importlib.util
import locale
import os
import sqlite3
import sys
from collections.abc import Generator, Sequence
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
from typing import Hashable, Optional, Union

import duckdb
import pandas as pd
import tzlocal
from typedstream.stream import TypedStreamReader

import ica.contact
from ica.contact import ContactRecord, get_contact_records
from ica.exceptions import (
    ContactNotFoundError,
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
SUPPORTED_OUTPUT_FORMAT_MAP = {
    "csv": "csv",
    "excel": "xlsx",
    "markdown": "md",
    "json": "json",
}


@dataclass
class DataFrameNamespace:
    """
    The namespace containing the relevant dataframes for the specified user in
    the chat database
    """

    messages: pd.DataFrame
    attachments: pd.DataFrame
    handles: pd.DataFrame


# iMessage stores dates as nanoseconds since 2001-01-01 (Apple's Core Data
# epoch), so we must precompute the difference between that and the Unix epoch
S_TO_NS = 1_000_000_000
IMESSAGE_EPOCH_NS_OFFSET = int(
    (
        datetime(2001, 1, 1, tzinfo=timezone.utc)
        - datetime(1970, 1, 1, tzinfo=timezone.utc)
    ).total_seconds()
    * S_TO_NS
)


def build_date_filter_clause(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    timezone: Optional[str] = None,
) -> str:
    """
    Build a SQL WHERE clause fragment to filter messages by date range.
    Dates are converted to iMessage's internal format (nanoseconds since 2001-01-01).
    The to_date filter uses < (exclusive) to match pandas behavior where comparing
    a datetime to a date string treats the string as midnight.
    """
    clauses = []
    if from_date:
        # Convert from_date to iMessage timestamp (nanoseconds since 2001-01-01)
        from_ts = pd.Timestamp(from_date, tz=timezone)
        # Use integer arithmetic for precision (pd.Timestamp.value is ns since
        # 1970)
        from_ns = from_ts.value - IMESSAGE_EPOCH_NS_OFFSET
        clauses.append(f'AND "message"."date" >= {from_ns}')
    if to_date:
        # Use midnight of to_date (exclusive) to match standard half-open
        # interval behavior (start <= date < end), preventing double-counting at
        # boundaries
        to_ts = pd.Timestamp(to_date, tz=timezone)
        # Use integer arithmetic for precision
        to_ns = to_ts.value - IMESSAGE_EPOCH_NS_OFFSET
        clauses.append(f'AND "message"."date" < {to_ns}')
    return " ".join(clauses)


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


def get_chat_ids_for_contacts(
    con: sqlite3.Connection, contact_records: Sequence[ContactRecord]
) -> list[str]:
    """
    Find the chat IDs for the chat(s) involving exactly the specified contacts.
    """

    # We need to construct a SQL query that finds chats where:
    # 1. The number of participants matches the number of contacts
    # 2. Each contact is represented by at least one of their handles in the
    #    chat

    contact_checks = []
    query_params = []

    for record in contact_records:
        identifiers = list(record.get_identifiers())
        if not identifiers:
            # If a contact has no identifiers, they can't be in a chat
            return []

        placeholders = ", ".join("?" for _ in identifiers)
        contact_checks.append(
            f"MAX(CASE WHEN handle.id IN ({placeholders}) THEN 1 ELSE 0 END)"
        )
        query_params.extend(identifiers)

    # The query ensures that the total participant count matches the number of
    # contacts, and that the number of *matched* contacts also equals the number
    # of contacts (implying every contact is present)
    query = f"""
    SELECT chat_id
    FROM chat_handle_join
    JOIN handle ON chat_handle_join.handle_id = handle.ROWID
    GROUP BY chat_id
    HAVING COUNT(handle.id) = ?
       AND ({" + ".join(contact_checks)}) = ?
    """

    # Add the count parameters (one for COUNT check, one for SUM check)
    full_params = [len(contact_records)] + query_params + [len(contact_records)]

    return [row[0] for row in con.execute(query, full_params).fetchall()]


def get_messages_dataframe(
    con: sqlite3.Connection,
    chat_ids: Sequence[str],
    contact_records: Sequence[ContactRecord],
    timezone: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Return a pandas dataframe representing all messages in a particular
    conversation (identified by the given phone number or email address)
    """
    # If no IANA timezone name is specified, default to the name of the system's
    # local timezone
    if not timezone:
        timezone = tzlocal.get_localzone().key

    chat_ids_placeholder = ", ".join(f"'{cid}'" for cid in chat_ids)
    date_filter_clause = build_date_filter_clause(
        from_date,
        to_date,
        timezone=timezone,
    )

    # Create a mapping from identifier to display name for efficient aggregation
    identifier_to_display_name = {}
    for record in contact_records:
        display_name = ica.contact.get_unique_contact_display_name(
            contact_records, record
        )
        for identifier in record.get_identifiers():
            identifier_to_display_name[identifier] = display_name

    return (
        pd.read_sql_query(
            sql=importlib.resources.files("ica")
            .joinpath(os.path.join("queries", "messages.sql"))
            .read_text()
            .format(
                chat_ids_placeholder=chat_ids_placeholder,
                date_filter_clause=date_filter_clause,
            ),
            con=con,
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
                df.loc[df["text"].isna(), "attributedBody"].apply(
                    decode_message_attributedbody
                )
            )
        )
        # Remove 'attributedBody' column now that it has been merged into the
        # 'text' column
        .drop(columns="attributedBody")
        # Use a regex-based heuristic to determine which messages are reactions
        .assign(
            is_reaction=lambda df: df["text"].str.match(
                r"^(Loved|Liked|Disliked|Laughed at|Emphasized|Questioned|Reacted)"
                r" (“(.*?)”|an \w+|(.*?) to “(.*?)”)$"
            )
        )
        # Convert 'is_from_me' values from integers to proper booleans
        .assign(is_from_me=lambda df: df["is_from_me"].astype(bool))
        # Add sender display name
        .assign(
            sender_display_name=lambda df: df["sender_handle"]
            .map(identifier_to_display_name)
            .fillna("Me")
            .where(df["is_from_me"].eq(False), "Me")
        )
    )


def resolve_sender_identifiers(
    contact_records: Sequence[ContactRecord],
    from_people: Sequence[str],
) -> tuple[bool, set[str]]:
    """
    Resolve the user-supplied 'from_people' filters into a set of allowed
    handle identifiers (e.g. phone numbers, email addresses)
    """
    include_me = False
    allowed_handles: set[str] = set()

    for person_filter in from_people:
        if person_filter.lower() == "me":
            include_me = True
            continue

        if person_filter.lower() == "them":
            for contact in contact_records:
                allowed_handles.update(contact.get_identifiers())
            continue

        # Check against contacts
        matching_contacts = []
        for contact in contact_records:
            # Check name (case-insensitive startswith)
            if contact.first_name.lower().startswith(
                person_filter.lower()
            ) or contact.full_name.lower().startswith(person_filter.lower()):
                matching_contacts.append(contact)
                continue

            # Check identifiers (exact match)
            if any(
                identifier.lower() == person_filter.lower()
                for identifier in contact.get_identifiers()
            ):
                matching_contacts.append(contact)
                continue

        if not matching_contacts:
            raise ContactNotFoundError(f"No contact found matching '{person_filter}'")

        # Add all identifiers for the matched contact
        allowed_handles.update(matching_contacts[0].get_identifiers())

    return include_me, allowed_handles


def filter_dataframe(
    df: pd.DataFrame,
    contact_records: Sequence[ContactRecord],
    from_people: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """
    Return a copy of the messages dataframe that has been filtered by the
    user-supplied from_people filter. Date filtering is handled at the SQL level.
    """

    # If no person filter is supplied, or if "all" is specified, return values
    # from all senders
    if not from_people or "all" in (p.lower() for p in from_people):
        return df

    include_me, allowed_handles = resolve_sender_identifiers(
        contact_records, from_people
    )

    return df.pipe(
        lambda df: df[
            (df["is_from_me"] & include_me)
            # In the macOS Messages database, the handle_id (and thus
            # sender_handle) for outgoing messages (is_from_me=1) in 1-on-1
            # chats refers to the recipient, not the sender. Therefore, we
            # must explicitly exclude messages from "me" when filtering by a
            # specific contact handle, otherwise we will inadvertently
            # include messages sent TO that contact.
            | (df["sender_handle"].isin(allowed_handles) & ~df["is_from_me"])
        ]
    )


def get_attachments_dataframe(
    con: sqlite3.Connection,
    chat_ids: Sequence[str],
    timezone: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Return a pandas dataframe representing all attachments in a particular
    conversation (identified by the given phone number)
    """
    chat_ids_placeholder = ", ".join(f"'{cid}'" for cid in chat_ids)
    date_filter_clause = build_date_filter_clause(
        from_date,
        to_date,
        timezone=timezone,
    )

    return (
        pd.read_sql_query(
            sql=importlib.resources.files("ica")
            .joinpath(os.path.join("queries", "attachments.sql"))
            .read_text()
            .format(
                chat_ids_placeholder=chat_ids_placeholder,
                date_filter_clause=date_filter_clause,
            ),
            con=con,
            parse_dates={"datetime": "ISO8601"},
        )
        # Expose the date/time of the message alongside each attachment record,
        # for convenience
        .assign(
            datetime=lambda df: df["datetime"]
            .dt.tz_localize("UTC")
            .dt.tz_convert(timezone)
        )
        .assign(is_from_me=lambda df: df["is_from_me"].astype(bool))
    )


def get_handles_dataframe(
    con: sqlite3.Connection,
    contact_records: Sequence[ContactRecord],
) -> pd.DataFrame:
    """
    Return a pandas dataframe representing the handles associated with the
    participants in a particular conversation. This allows for easy joining with
    the messages dataframe.
    """
    # 1. Collect all identifiers to query
    all_identifiers = set()
    for record in contact_records:
        all_identifiers.update(record.get_identifiers())

    if not all_identifiers:
        return pd.DataFrame(
            columns=pd.Index(
                [
                    "handle_id",
                    "first_name",
                    "last_name",
                    "identifier",
                    "contact_id",
                    "display_name",
                ]
            )
        )

    # 2. Query for handle IDs
    placeholders = ", ".join("?" for _ in all_identifiers)
    query = f"SELECT id, ROWID FROM handle WHERE id IN ({placeholders})"

    # Map identifier string -> handle_id (int)
    # Note: handle.id is the string (phone/email), handle.ROWID is the int
    handle_map = dict(con.execute(query, list(all_identifiers)).fetchall())

    # 3. Build rows for the dataframe
    return pd.DataFrame(
        [
            {
                "handle_id": handle_map[identifier],
                "name": getattr(
                    record,
                    "full_name",
                    f"{record.first_name} {record.last_name}".strip(),
                ),
                "first_name": record.first_name,
                "last_name": record.last_name,
                "identifier": identifier,
                "contact_id": record.id,
                "display_name": ica.contact.get_unique_contact_display_name(
                    contact_records, record
                ),
            }
            for record in contact_records
            for identifier in record.get_identifiers()
            if identifier in handle_map
        ]
    )


def get_dataframes(
    contacts: Sequence[str],
    timezone: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    from_people: Optional[Sequence[str]] = None,
) -> DataFrameNamespace:
    """
    Return all dataframes for a specific macOS Messages conversation
    """
    # Validate date range before querying
    if from_date and to_date and pd.Timestamp(from_date) > pd.Timestamp(to_date):
        raise DateRangeInvalidError("Date range is backwards")

    contact_records = get_contact_records(contacts)

    with closing(sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)) as con:
        chat_ids = get_chat_ids_for_contacts(con, contact_records)
        if not chat_ids:
            raise ConversationNotFoundError(
                'No conversation found for the contact(s) "{}"'.format(
                    ", ".join(contacts)
                )
            )

        dfs = DataFrameNamespace(
            messages=get_messages_dataframe(
                con, chat_ids, contact_records, timezone, from_date, to_date
            ),
            attachments=get_attachments_dataframe(
                con, chat_ids, timezone, from_date, to_date
            ),
            handles=get_handles_dataframe(con, contact_records),
        )
        # Date filtering is now done in SQL; filter_dataframe only handles
        # from_people filtering
        dfs.messages = filter_dataframe(
            dfs.messages,
            contact_records,
            from_people=from_people,
        )
        dfs.attachments = filter_dataframe(
            dfs.attachments,
            contact_records,
            from_people=from_people,
        )
        return dfs


def prettify_header_name(
    header_name: Hashable, prettified_label_overrides: Optional[dict[str, str]] = None
) -> Hashable:
    """
    Format the given header name to be more human-readable (e.g. "foo_bar" =>
    "Foo Bar")
    """
    if prettified_label_overrides and header_name in prettified_label_overrides:
        return prettified_label_overrides[header_name]

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


def make_dataframe_tz_naive(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all of the datetime timstamps in the given dataframe to be
    timezone-naive, including all columns and the index
    """
    return df.pipe(
        lambda df: (
            df.set_index(df.index.tz_localize(None))
            if isinstance(df.index, pd.DatetimeIndex)
            else df
        )
    ).assign(
        **{
            col: df[col].dt.tz_localize(None)
            for col in df.select_dtypes(include=["datetime64[ns, UTC]"])
        }
    )


def prepare_df_for_output(
    df: pd.DataFrame, prettified_label_overrides: Optional[dict[str, str]] = None
) -> pd.DataFrame:
    """
    Prepare the given dataframe for output by prettifying column names,
    stripping timezone details incompatible with Excel, and other normalization
    operations; return the normalized dataframe
    """

    return (
        df.rename(
            # Prettify header column (i.e. textual values in first column)
            index=functools.partial(
                prettify_header_name,
                prettified_label_overrides=prettified_label_overrides,
            ),
            # Prettify header row (i.e. column names)
            columns=functools.partial(
                prettify_header_name,
                prettified_label_overrides=prettified_label_overrides,
            ),
        )
        # Prettify index column name
        .rename_axis(
            index=prettify_header_name(df.index.name, prettified_label_overrides)
        )
        # Make all indices start from 1 instead of 0, but only if the index is
        # the default (rather than a custom column)
        .pipe(lambda df: df.set_index(df.index + 1 if not df.index.name else df.index))
        # Make dataframe timestamps timezone-naive (which is required for
        # exporting to Excel)
        .pipe(lambda df: make_dataframe_tz_naive(df))
    )


def output_results(
    analyzer_df: pd.DataFrame,
    format: Optional[str] = None,
    output: Union[str, StringIO, BytesIO, None] = None,
    prettified_label_overrides: Optional[dict[str, str]] = None,
) -> None:
    """
    Print the dataframe provided by an analyzer module
    """
    # Set the locale to the user's default setting to ensure that numbers are
    # formatted correctly (e.g. with thousands separators); however, if the
    # locale has already been set (e.g. by a test), do not override it
    with contextlib.suppress(locale.Error):
        if locale.getlocale(locale.LC_NUMERIC) == (None, None):
            locale.setlocale(locale.LC_ALL, "")

    is_default_index = not analyzer_df.index.name
    output_df = prepare_df_for_output(
        analyzer_df, prettified_label_overrides=prettified_label_overrides
    )

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
    elif format == "json":
        json_output_df = (
            # Reset index if it's to be included in output
            output_df.reset_index() if output_args.get("index") else output_df
        )
        json_output_df.to_json(output, orient="records", date_format="iso", indent=2)
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
            .rename_axis(columns=output_df.index.name)
            .rename_axis(index=None)
            .to_string(
                output,
                index=True,
                line_width=100000,
                # Format numbers with thousands separators
                formatters={
                    col: "{:n}".format
                    for col in output_df.select_dtypes(include="number").columns
                },
            )
        )

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
def execute_sql_query(query: str, con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Execute the given arbitrary SQL query, provided a connection to the
    in-memory DuckDB database created by ica.get_sql_connection()
    """
    return con.execute(query).df()
