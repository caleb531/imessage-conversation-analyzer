#!/usr/bin/env python3
"""global test fixtures and helper methods"""

import base64
import contextlib
import glob
import json
import os
import os.path
import shutil
import sqlite3
import tempfile
from collections.abc import Generator
from typing import Any, Literal, Union
from unittest import TestCase
from unittest.mock import patch

# Disable maximum length of test diff output for all tests (source:
# <https://stackoverflow.com/a/23617918/560642>)
TestCase.maxDiff = None

MockDatabaseName = Union[Literal["chats"], Literal["contacts"]]

# When running tests, point to mock sqlite3 database instead of the default
# macOS chat.db under ~/Library
temp_dir = tempfile.gettempdir()
temp_db_dir = os.path.join(temp_dir, "ica")

mock_contacts_db_glob = os.path.join(temp_db_dir, "*.abcddb")
mock_contacts_db_path = mock_contacts_db_glob.replace("*", "addressbook")
contacts_db_glob_patcher = patch("ica.contact.DB_GLOB", mock_contacts_db_glob)

mock_chats_db_path = os.path.join(temp_db_dir, "chat.db")
chats_db_path_patcher = patch("ica.core.DB_PATH", mock_chats_db_path)


# A string prefix that can be placed at the beginning of any JSON string within
# the mock data to indicate that the rest of the string is base64
BASE64_PREFIX = "base64:"


def set_up() -> None:
    """global setup fixture for all tests"""
    tear_down()  # in case something prevents tear_down() from running normally
    contacts_db_glob_patcher.start()
    chats_db_path_patcher.start()
    with contextlib.suppress(OSError):
        os.makedirs(temp_db_dir)
    create_mock_db("contacts", mock_contacts_db_path)
    create_mock_db("chats", mock_chats_db_path)


def tear_down() -> None:
    """global teardown fixture for all tests"""
    with contextlib.suppress(OSError):
        shutil.rmtree(temp_db_dir)
    chats_db_path_patcher.stop()
    contacts_db_glob_patcher.stop()


def format_record_value(
    value: Union[str, int, float, bool]  # JSON strings are always UTF-8
) -> Union[str, bytes, int, float, bool]:
    """
    Format the value of a mock database record, including decoding it if it's
    base64
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
    """Retrieve the JSON mock data for the DB table with the given name"""
    for data_path in glob.iglob(f"tests/data/dbs/{db_name}/*.json"):
        table_name = os.path.splitext(os.path.basename(data_path))[0]
        with open(data_path, "r") as data_file:
            records = json.load(data_file)
            yield table_name, [
                {key: format_record_value(value) for key, value in record.items()}
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
