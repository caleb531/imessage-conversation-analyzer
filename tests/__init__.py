#!/usr/bin/env python3
"""global test fixtures and helper methods"""

import contextlib
import json
import os
import os.path
import shutil
import sqlite3
import tempfile
from collections.abc import Generator
from typing import Any
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


def get_mock_db_data_for_table(table_name: str) -> list[dict]:
    """Retrieve the JSON mock data for the DB table with the given name"""
    with open(f"tests/data/{table_name}.json", "r") as data_file:
        return json.load(data_file)


@contextlib.contextmanager
def mock_database() -> Generator[sqlite3.Connection, Any, Any]:
    """Create and populate a mock messages database"""
    messages = get_mock_db_data_for_table("message")
    with sqlite3.connect(mock_db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(f"CREATE TABLE message({', '.join(messages[0].keys())})")

        key_placeholders = ", ".join(f":{key}" for key in messages[0].keys())
        cursor.executemany(f"INSERT INTO message VALUES({key_placeholders})", messages)
        connection.commit()
        yield connection
