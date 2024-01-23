#!/usr/bin/env python3
"""global test fixtures and helper methods"""

import contextlib
import json
import os
import os.path
import shutil
import sqlite3
import tempfile
import typing
from unittest.mock import patch

# When running tests, point to mock sqlite3 database instead of the default
# macOS chat.db under ~/Library
temp_dir = tempfile.gettempdir()
temp_db_dir = os.path.join(temp_dir, "ica")
mock_db_path = os.path.join(temp_db_dir, "chat.db")
db_path_patcher = patch("ica.core.DB_PATH", mock_db_path)


def set_up() -> None:
    """global setup fixture for all tests"""
    db_path_patcher.start()
    with contextlib.suppress(OSError):
        os.makedirs(temp_db_dir)


def tear_down() -> None:
    """global teardown fixture for all tests"""
    with contextlib.suppress(OSError):
        shutil.rmtree(temp_db_dir)
    db_path_patcher.stop()


def get_db_mock_data_for_table(table_name: str) -> list[dict]:
    """Retrieve the JSON mock data for the DB table with the given name"""
    with open(f"tests/data/{table_name}.json", "r") as data_file:
        return json.load(data_file)


def format_value_for_db(value: str) -> str:
    """Format the given value for storage in the mock messages database"""
    if type(value) is bool:
        return str(int(value))
    else:
        return f"'{value}'"


@contextlib.contextmanager
def mock_database() -> typing.Generator:
    """Create and populate a mock messages database"""
    messages = get_db_mock_data_for_table("message")
    with sqlite3.connect(mock_db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(f"CREATE TABLE message({', '.join(messages[0].keys())})")
        values = ", ".join(
            ", ".join(format_value_for_db(value) for value in message.values())
            for message in messages
        )
        cursor.execute(f"INSERT INTO message VALUES({values})")
        connection.commit()
        yield
