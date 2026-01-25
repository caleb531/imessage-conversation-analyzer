import sqlite3
from collections.abc import Generator
from contextlib import closing

import pandas as pd
import pytest

from ica.contact import ContactRecord
from ica.core import get_handles_dataframe
from tests.conftest import mock_chats_db_path


@pytest.fixture
def mock_db_connection() -> Generator[sqlite3.Connection, None, None]:
    with closing(
        sqlite3.connect(f"file:{mock_chats_db_path}?mode=ro", uri=True)
    ) as con:
        yield con


def test_get_handles_dataframe(mock_db_connection: sqlite3.Connection) -> None:
    contact_records = [
        ContactRecord(
            id="1",
            first_name="Jane",
            last_name="Fernbrook",
            phone_numbers=["+12234567890"],
            email_addresses=[],
        ),
        ContactRecord(
            id="2",
            first_name="John",
            last_name="Doe",
            phone_numbers=[],
            email_addresses=["john.doe@example.com"],
        ),
    ]

    handles = get_handles_dataframe(mock_db_connection, contact_records)

    assert isinstance(handles, pd.DataFrame)
    # John Doe is not in the mock DB, so he won't appear in the result
    assert len(handles) == 1
    assert list(handles.columns) == [
        "handle_id",
        "name",
        "first_name",
        "last_name",
        "identifier",
        "contact_id",
        "display_name",
    ]

    # Check Jane's row
    jane_row = handles[handles["first_name"] == "Jane"].iloc[0]
    assert jane_row["name"] == "Jane Fernbrook"
    assert jane_row["identifier"] == "+12234567890"
    assert isinstance(jane_row["handle_id"], str)
    # unless we add him. The current implementation filters out handles not found in DB.
    # Let's check if John is in the result. If not, we should update the test
    # expectation.

    # Actually, let's use a contact that IS in the mock DB to be safe.
    # Daniel Brightingale is in the mock DB.

    contact_records_2 = [
        ContactRecord(
            id="1",
            first_name="Daniel",
            last_name="Brightingale",
            phone_numbers=["+12123456789"],
            email_addresses=[],
        )
    ]

    handles_2 = get_handles_dataframe(mock_db_connection, contact_records_2)
    assert len(handles_2) == 1
    daniel_row = handles_2.iloc[0]
    assert daniel_row["name"] == "Daniel Brightingale"
    assert daniel_row["identifier"] == "+12123456789"


def test_get_handles_dataframe_empty(mock_db_connection: sqlite3.Connection) -> None:
    handles = get_handles_dataframe(mock_db_connection, [])
    assert handles.empty
    assert list(handles.columns) == [
        "handle_id",
        "first_name",
        "last_name",
        "identifier",
        "contact_id",
        "display_name",
    ]
