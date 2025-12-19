#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures.

This file is automatically discovered by pytest. Any fixtures defined here
are available to ALL test files without importing!
"""

import contextlib
import shutil
from collections.abc import Generator
from pathlib import Path
from tempfile import gettempdir
from unittest.mock import patch

import duckdb
import pytest

from tests.mock_db_utils import create_mock_db

# Setup paths (from utils.py)
temp_ica_dir = Path(gettempdir()) / "ica"
mock_contacts_db_glob = temp_ica_dir / "*.abcddb"
mock_contacts_db_path = mock_contacts_db_glob.with_name("addressbook.abcddb")
mock_chats_db_path = temp_ica_dir / "chat.db"


@pytest.fixture(autouse=True)
def keep_duckdb_connections_alive() -> Generator[None, None, None]:
    """
    Keep DuckDB connections alive during tests to prevent them from being
    garbage collected and closed before the test can inspect the results.
    """
    connections = []
    original_connect = duckdb.connect

    def mock_connect(*args, **kwargs):
        con = original_connect(*args, **kwargs)
        connections.append(con)
        return con

    with patch("duckdb.connect", side_effect=mock_connect):
        yield

    for con in connections:
        with contextlib.suppress(Exception):
            con.close()


@pytest.fixture(autouse=True)
def setup_mock_databases() -> Generator[None, None, None]:
    """
    Setup and teardown mock databases for each test.

    This fixture runs automatically for EVERY test function because
    of autouse=True. No decorators or inheritance needed!
    """
    # Cleanup first (in case of previous test interruption)
    with contextlib.suppress(OSError):
        shutil.rmtree(temp_ica_dir)

    # Start patching and create databases
    with (
        patch("ica.contact.DB_GLOB", mock_contacts_db_glob),
        patch("ica.core.DB_PATH", mock_chats_db_path),
    ):
        # Setup
        with contextlib.suppress(OSError):
            temp_ica_dir.mkdir(parents=True, exist_ok=True)
        create_mock_db("contacts", mock_contacts_db_path)
        create_mock_db("chats", mock_chats_db_path)

        # This is where the test runs
        yield

        # Teardown
        with contextlib.suppress(OSError):
            shutil.rmtree(temp_ica_dir)
