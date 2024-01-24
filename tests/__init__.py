#!/usr/bin/env python3
"""global test fixtures and helper methods"""


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
from unittest.mock import patch

MockDatabaseName = Union[Literal["chats"], Literal["contacts"]]

# When running tests, point to mock sqlite3 database instead of the default
# macOS chat.db under ~/Library
temp_dir = tempfile.gettempdir()
temp_db_dir = os.path.join(temp_dir, "ica")

mock_contacts_db_path = os.path.join(temp_db_dir, "addressbook.abcddb")
mock_contacts_db_glob = os.path.join(temp_db_dir, "*.abcddb")
contacts_db_glob_patcher = patch("ica.contact.DB_GLOB", mock_contacts_db_glob)

mock_chats_db_path = os.path.join(temp_db_dir, "chat.db")
chats_db_path_patcher = patch("ica.core.DB_PATH", mock_chats_db_path)


def set_up() -> None:
    """global setup fixture for all tests"""
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


def get_mock_data_for_db(
    db_name: MockDatabaseName,
) -> Generator[tuple[str, list[dict]], Any, Any]:
    """Retrieve the JSON mock data for the DB table with the given name"""
    for data_path in glob.iglob(f"tests/data/{db_name}/*.json"):
        table_name = os.path.splitext(os.path.basename(data_path))[0]
        with open(f"tests/data/{db_name}/{table_name}.json", "r") as data_file:
            records = json.load(data_file)
            yield table_name, records


def create_mock_db(db_name: MockDatabaseName, db_path: str) -> None:
    """Create and populate a mock database with the given name and path"""
    with sqlite3.connect(db_path) as con:
        for table_name, records in get_mock_data_for_db(db_name):
            cur = con.cursor()
            cur.execute(f"CREATE TABLE {table_name}({', '.join(records[0].keys())})")
            key_placeholders = ", ".join(f":{key}" for key in records[0].keys())
            cur.executemany(
                f"INSERT INTO {table_name} VALUES({key_placeholders})", records
            )
            con.commit()
