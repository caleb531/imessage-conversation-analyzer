#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

from pathlib import Path
from tempfile import gettempdir

import pytest

import ica
from ica.contact import (
    ContactRecord,
    coalesce_contact_records,
    get_unique_contact_display_name,
)
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
    """
    Should raise a ContactNotFoundError when at least one contact is missing, even
    if others are valid.
    """
    # "Thomas Riverstone" exists in the mock DB, "Imaginary Person" does not.
    # This ensures we catch partial failures.
    with pytest.raises(ica.ContactNotFoundError) as excinfo:
        ica.get_dataframes(contacts=["Thomas Riverstone", "Imaginary Person"])

    error_msg = str(excinfo.value)
    # The error should mention the missing contact
    assert "Imaginary Person" in error_msg
    # The error generally shouldn't mention the found contact (though checking
    # for its absence defends against "No contact found for Thomas, Imaginary")
    assert "Thomas Riverstone" not in error_msg


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


def test_messages_include_expressive_send_style_id() -> None:
    """
    Should include the raw expressive send style ID from the chat DB.
    """
    dfs = ica.get_dataframes(contacts=["Daniel Brightingale"])
    assert "expressive_send_style_id" in dfs.messages.columns
    assert (
        dfs.messages.loc[
            dfs.messages["ROWID"] == "67d1d980-4db8-4005-b644-cd269402dd29",
            "expressive_send_style_id",
        ].iloc[0]
        == "com.apple.messages.effect.CKEchoEffect"
    )


def test_contact_record_merging() -> None:
    """
    Should merge contact records if two records share the same name and share at
    least one common identifier.
    """
    # Create a duplicate contacts database to simulate multiple sources
    # containing the same contact name
    duplicate_db_path = Path(gettempdir()) / "ica" / "duplicate.abcddb"
    create_mock_db("contacts", duplicate_db_path)

    # The duplicate database contains the same contact "Daniel Brightingale"
    # with the same phone number. The coalescing logic should merge these
    # into a single record, so no error should be raised.
    ica.get_dataframes(contacts=["Daniel Brightingale"])


@pytest.mark.mock_db_config(
    contacts={
        "ZABCDRECORD": [
            {"Z_PK": 1, "ZFIRSTNAME": "Daniel", "ZLASTNAME": "Brightingale"},
            {"Z_PK": 2, "ZFIRSTNAME": "Daniel", "ZLASTNAME": "Brightingale"},
        ],
        "ZABCDPHONENUMBER": [
            {"ZOWNER": 1, "ZFULLNUMBER": "212-345-6789"},
            {"ZOWNER": 2, "ZFULLNUMBER": "555-999-9999"},
        ],
    }
)
def test_contact_with_same_name_error() -> None:
    """
    Should raise ContactWithSameNameError if multiple contacts share the same name
    but have completely different identifiers.
    """
    with pytest.raises(ica.ContactWithSameNameError):
        ica.get_dataframes(contacts=["Daniel Brightingale"])


def test_coalesce_contact_records_name_merging() -> None:
    """
    Should merge first and last names when coalescing contact records if the
    existing record has missing name fields.
    """
    records = [
        # Case 1: Existing record has no first name, new record does
        ContactRecord(
            id="1", first_name="", last_name="Pinerose", phone_numbers=["123"]
        ),
        ContactRecord(
            id="2", first_name="Jennifer", last_name="", phone_numbers=["123"]
        ),
        # Case 2: Existing record has no last name, new record does
        ContactRecord(id="3", first_name="Jen", last_name="", phone_numbers=["456"]),
        ContactRecord(
            id="4", first_name="", last_name="Windhelm", phone_numbers=["456"]
        ),
        # Case 3: Existing record has names, new record has different names
        # (should preserve existing)
        ContactRecord(
            id="5", first_name="Alice", last_name="Wonderland", phone_numbers=["789"]
        ),
        ContactRecord(
            id="6", first_name="Bob", last_name="Builder", phone_numbers=["789"]
        ),
        # Case 4: Existing record has no ID, new record does
        ContactRecord(
            id="7",
            first_name="Charlie",
            last_name="Watermarsh",
            phone_numbers=["+15550000000"],
        ),
        ContactRecord(
            id="8",
            first_name="Charlie",
            last_name="Watermarsh",
            phone_numbers=["+15550000000"],
        ),
    ]

    coalesced = coalesce_contact_records(records)

    assert len(coalesced) == 4

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

    # Check Case 4
    record4 = next(r for r in coalesced if "+15550000000" in r.phone_numbers)
    assert record4.id == "8"


def test_get_unique_contact_display_name_unique_first_name() -> None:
    """
    Should return the first name if it is unique among the contact records.
    """
    records = [
        ContactRecord(id="1", first_name="Alice", last_name="Smith"),
        ContactRecord(id="2", first_name="Bob", last_name="Jones"),
    ]
    display_name = get_unique_contact_display_name(records, records[0])
    assert display_name == "Alice"


def test_get_unique_contact_display_name_duplicate_first_name() -> None:
    """
    Should return the full name if the first name is not unique.
    """
    records = [
        ContactRecord(id="1", first_name="Alice", last_name="Smith"),
        ContactRecord(id="2", first_name="Alice", last_name="Jones"),
    ]
    display_name = get_unique_contact_display_name(records, records[0])
    assert display_name == "Alice Smith"


def test_get_unique_contact_display_name_duplicate_full_name() -> None:
    """
    Should return the phone number if the full name is not unique.
    """
    records = [
        ContactRecord(
            id="1",
            first_name="Alice",
            last_name="Smith",
            phone_numbers=["+15551234567"],
        ),
        ContactRecord(
            id="2",
            first_name="Alice",
            last_name="Smith",
            phone_numbers=["+15559876543"],
        ),
    ]
    display_name = get_unique_contact_display_name(records, records[0])
    assert display_name == "+15551234567"


def test_get_unique_contact_display_name_email_fallback() -> None:
    """
    Should return the email address if the contact has no phone number and the
    name is not unique.
    """
    records = [
        ContactRecord(
            id="1",
            first_name="Alice",
            last_name="Smith",
            phone_numbers=[],
            email_addresses=["alice.smith@example.com"],
        ),
        ContactRecord(
            id="2",
            first_name="Alice",
            last_name="Smith",
            phone_numbers=["+15551234567"],
            email_addresses=[],
        ),
    ]
    display_name = get_unique_contact_display_name(records, records[0])
    assert display_name == "alice.smith@example.com"


def test_get_unique_contact_display_name_fallback() -> None:
    """
    Should fall back to full name if all identifiers are duplicates (unlikely
    but possible).
    """
    records = [
        ContactRecord(
            id="1",
            first_name="Alice",
            last_name="Smith",
            phone_numbers=["+15551234567"],
            email_addresses=["alice.smith@example.com"],
        ),
        ContactRecord(
            id="2",
            first_name="Alice",
            last_name="Smith",
            phone_numbers=["+15551234567"],
            email_addresses=["alice.smith@example.com"],
        ),
    ]
    display_name = get_unique_contact_display_name(records, records[0])
    assert display_name == "Alice Smith"
