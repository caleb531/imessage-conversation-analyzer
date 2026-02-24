#!/usr/bin/env python3
"""Utilities for creating the mock databases used for testing"""

import base64
import glob
import json
import sqlite3
from collections.abc import Generator
from contextlib import closing
from pathlib import Path
from typing import Any, Literal, Optional, Union

MockDatabaseName = Union[Literal["chats"], Literal["contacts"]]

# A string prefix that can be placed at the beginning of any JSON string within
# the mock data to indicate that the rest of the string is base64
BASE64_PREFIX = "base64:"


def parse_record_value(
    # JSON strings are always UTF-8, so a `bytes` string would never be passed
    # as one of the JSON values to format
    value: Union[str, int, float, bool],
) -> Union[str, bytes, int, float, bool]:
    """
    Parse the value of a mock database record, decoding the value if it's
    base64, and simply passing it through otherwise
    """
    if type(value) is str and str(value).startswith(BASE64_PREFIX):
        return base64.standard_b64decode(
            value.removeprefix(BASE64_PREFIX).encode("utf-8")
        )
    else:
        return value


def get_mock_data_for_db(
    db_name: MockDatabaseName,
) -> Generator[tuple[str, list[dict]], Any, Any]:
    """Retrieve all JSON mock table data for the DB with the given name"""
    for data_path in glob.iglob(f"tests/data/dbs/{db_name}/*.json"):
        table_name = Path(data_path).stem
        records = json.loads(Path(data_path).read_text())
        yield (
            table_name,
            [
                {key: parse_record_value(value) for key, value in record.items()}
                for record in records
            ],
        )


def create_mock_db(
    db_name: MockDatabaseName,
    db_path: Path,
    db_contents: Optional[dict[str, list[dict]]] = None,
) -> None:
    """
    Create and populate a mock database with the given name and path.

    Args:
        db_name: The type of database ("chats" or "contacts")
        db_path: Where to create the SQLite file
        db_contents: Optional dictionary of table contents to merge with the
            default file-loaded tables. keys are table names, values are lists
            of row dictionaries.
    """
    merged_data = {**dict(get_mock_data_for_db(db_name)), **(db_contents or {})}

    with closing(sqlite3.connect(db_path)) as con:
        for table_name, records in merged_data.items():
            if not len(records):
                continue
            all_keys = list(dict.fromkeys(key for record in records for key in record))
            normalized_records = [
                {key: record.get(key) for key in all_keys} for record in records
            ]
            with closing(con.cursor()) as cur:
                cur.execute(f"CREATE TABLE {table_name}({', '.join(all_keys)})")
                key_placeholders = ", ".join(f":{key}" for key in all_keys)
                cur.executemany(
                    f"INSERT INTO {table_name} VALUES({key_placeholders})",
                    normalized_records,
                )
            con.commit()
