#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import sqlite3
from pathlib import Path
from tempfile import gettempdir

import pytest

import ica
from ica.contact import ContactRecord, coalesce_contact_records
from tests.mock_db_utils import create_mock_db


def test_find_conversation_via_phone_number_only() -> None:
    """
    Should find conversation for contact with phone number only.
    """
    dfs = ica.get_dataframes(contacts=["Daniel Brightingale"])
    assert len(dfs.messages) > 0


def test_find_conversation_via_email_address_only() -> None:
    """
    Should find conversation for contact with email address only.
    """
    dfs = ica.get_dataframes(contacts=["Thomas Riverstone"])
    assert len(dfs.messages) > 0


def test_has_contact_info_but_no_conversation() -> None:
    """
    Should raise a ConversationNotFoundError if contact has info but no
    conversation.
    """
    with pytest.raises(ica.ConversationNotFoundError):
        ica.get_dataframes(contacts=["Evelyn Oakhaven"])


def test_no_contact_info() -> None:
    """
    Should raise a ConversationNotFoundError if contact is missing info (so
    implicitly no chat, either)
    """
    with pytest.raises(ica.ConversationNotFoundError):
        ica.get_dataframes(contacts=["Matthew Whisperton"])


def test_contact_not_found_error() -> None:
    """Should raise a ContactNotFoundError when a contact is not found."""
    with pytest.raises(ica.ContactNotFoundError):
        ica.get_dataframes(contacts=["Imaginary Person"])


@pytest.mark.parametrize(
    "phone_number",
    (
        "212-345-6789",
        "2123456789",
        "(212) 345-6789",
        "+1 212-345-6789",
        "+1 (212) 345-6789",
        "1-212-345-6789",
    ),
)
def test_find_conversation_via_phone_number_lookup(phone_number: str) -> None:
    """
    Should find conversation by searching for the phone number directly.
    """
    dfs = ica.get_dataframes(contacts=[phone_number])
    assert len(dfs.messages) > 0


@pytest.mark.parametrize(
    "email_address",
    (
        "thomas.riverstone@example.com",
        "   thomas.riverstone@example.com   ",
    ),
)
def test_find_conversation_via_email_lookup(email_address: str) -> None:
    """
    Should find conversation by searching for the email address directly.
    """
    dfs = ica.get_dataframes(contacts=[email_address])
    assert len(dfs.messages) > 0


def test_find_group_conversation() -> None:
    """
    Should find conversation for a group chat.
    """
    dfs = ica.get_dataframes(contacts=["Daniel Brightingale", "Jane Fernbrook"])
    assert len(dfs.messages) > 0
    assert "Hello everyone!" in dfs.messages["text"].values


def test_duplicate_contact_name_error() -> None:
    """
    Should raise ContactWithSameNameError if multiple contacts share the same name.
    """
    # Create a duplicate contacts database to simulate multiple sources
    # containing the same contact name
    duplicate_db_path = Path(gettempdir()) / "ica" / "duplicate.abcddb"
    create_mock_db("contacts", duplicate_db_path)

    # The duplicate database contains the same contact "Daniel Brightingale"
    # with the same phone number. The coalescing logic should merge these
    # into a single record, so no error should be raised.
    ica.get_dataframes(contacts=["Daniel Brightingale"])


def test_contact_with_same_name_error() -> None:
    """
    Should raise ContactWithSameNameError if multiple contacts share the same name
    but have completely different identifiers.
    """
    # Create a duplicate contacts database
    duplicate_db_path = Path(gettempdir()) / "ica" / "duplicate_diff.abcddb"

    # We need to manually insert a record with the same name but different phone
    with sqlite3.connect(duplicate_db_path) as con:
        con.execute(
            "CREATE TABLE ZABCDRECORD (Z_PK INTEGER PRIMARY KEY, ZFIRSTNAME TEXT, ZLASTNAME TEXT)"  # noqa: E501
        )
        con.execute("CREATE TABLE ZABCDPHONENUMBER (ZOWNER INTEGER, ZFULLNUMBER TEXT)")
        con.execute("CREATE TABLE ZABCDEMAILADDRESS (ZOWNER INTEGER, ZADDRESS TEXT)")

        # Insert "Daniel Brightingale" but with a different phone number
        con.execute("INSERT INTO ZABCDRECORD VALUES (1, 'Daniel', 'Brightingale')")
        con.execute("INSERT INTO ZABCDPHONENUMBER VALUES (1, '555-999-9999')")
        con.commit()

    with pytest.raises(ica.ContactWithSameNameError):
        ica.get_dataframes(contacts=["Daniel Brightingale"])


def test_coalesce_contact_records_name_merging() -> None:
    """
    Should merge first and last names when coalescing contact records if the
    existing record has missing name fields.
    """
    records = [
        # Case 1: Existing record has no first name, new record does
        ContactRecord(first_name="", last_name="Pinerose", phone_numbers=["123"]),
        ContactRecord(first_name="Jennifer", last_name="", phone_numbers=["123"]),
        # Case 2: Existing record has no last name, new record does
        ContactRecord(first_name="Jen", last_name="", phone_numbers=["456"]),
        ContactRecord(first_name="", last_name="Windhelm", phone_numbers=["456"]),
        # Case 3: Existing record has names, new record has different names
        # (should preserve existing)
        ContactRecord(
            first_name="Alice", last_name="Wonderland", phone_numbers=["789"]
        ),
        ContactRecord(first_name="Bob", last_name="Builder", phone_numbers=["789"]),
    ]

    coalesced = coalesce_contact_records(records)

    assert len(coalesced) == 3

    # Check Case 1
    record1 = next(r for r in coalesced if "123" in r.phone_numbers)
    assert record1.first_name == "Jennifer"
    assert record1.last_name == "Pinerose"

    # Check Case 2
    record2 = next(r for r in coalesced if "456" in r.phone_numbers)
    assert record2.first_name == "Jen"
    assert record2.last_name == "Windhelm"

    # Check Case 3
    record3 = next(r for r in coalesced if "789" in r.phone_numbers)
    assert record3.first_name == "Alice"
    assert record3.last_name == "Wonderland"
