#!/usr/bin/env python3
"""Utilities for creating the mock databases used for testing"""


import base64
import glob
import json
import os
import os.path
import sqlite3
from collections.abc import Generator
from pathlib import Path
from typing import Any, Literal, Union

MockDatabaseName = Union[Literal["chats"], Literal["contacts"]]

# A string prefix that can be placed at the beginning of any JSON string within
# the mock data to indicate that the rest of the string is base64
BASE64_PREFIX = "base64:"


def parse_record_value(
    # JSON strings are always UTF-8, so a `bytes` string would never be passed
    # as one of the JSON values to format
    value: Union[str, int, float, bool]
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
        table_name = os.path.splitext(os.path.basename(data_path))[0]
        records = json.loads(Path(data_path).read_text())
        yield table_name, [
            {key: parse_record_value(value) for key, value in record.items()}
            for record in records
        ]


def create_mock_db(db_name: MockDatabaseName, db_path: str) -> None:
    """Create and populate a mock database with the given name and path"""
    with sqlite3.connect(db_path) as con:
        for table_name, records in get_mock_data_for_db(db_name):
            if not len(records):
                continue
            cur = con.cursor()
            cur.execute(f"CREATE TABLE {table_name}({', '.join(records[0].keys())})")
            key_placeholders = ", ".join(f":{key}" for key in records[0].keys())
            cur.executemany(
                f"INSERT INTO {table_name} VALUES({key_placeholders})", records
            )
            con.commit()
