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
from typing import Optional
from unittest.mock import patch

import pytest

from tests.mock_db_utils import create_mock_db

# Setup paths (from utils.py)
temp_ica_dir = Path(gettempdir()) / "ica"
mock_contacts_db_glob = temp_ica_dir / "*.abcddb"
mock_contacts_db_path = mock_contacts_db_glob.with_name("addressbook.abcddb")
mock_chats_db_path = temp_ica_dir / "chat.db"


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "mock_db_config(contacts, chats): Configure mock databases. "
        "Pass None to disable, or a dict to override table data.",
    )


@pytest.fixture(autouse=True)
def setup_mock_databases(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """
    Setup and teardown mock databases for each test.

    This fixture runs automatically for EVERY test function because
    of autouse=True. No decorators or inheritance needed!

    Use @pytest.mark.mock_db_config(chats={"message": [...]}) to override data.
    """
    # Default configuration
    config: dict[str, Optional[dict]] = {"contacts": {}, "chats": {}}

    # Update with marker configuration if present
    if marker := request.node.get_closest_marker("mock_db_config"):
        if marker.args:
            raise pytest.UsageError(
                f"mock_db_config accepts only keyword arguments (contacts, chats), "
                f"got positional args: {marker.args}"
            )

        unknown_keys = set(marker.kwargs) - config.keys()
        if unknown_keys:
            raise pytest.UsageError(
                f"mock_db_config got unknown arguments: {unknown_keys}. "
                f"Allowed: {list(config.keys())}"
            )

        config.update(marker.kwargs)

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

        # Create Contacts DB
        contacts_cfg = config.get("contacts")
        if contacts_cfg is not None:
            create_mock_db("contacts", mock_contacts_db_path, db_contents=contacts_cfg)

        # Create Chats DB
        chats_cfg = config.get("chats")
        if chats_cfg is not None:
            create_mock_db("chats", mock_chats_db_path, db_contents=chats_cfg)

        # This is where the test runs
        yield

        # Teardown
        with contextlib.suppress(OSError):
            shutil.rmtree(temp_ica_dir)
