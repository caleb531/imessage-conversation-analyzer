#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import pytest

import ica


def test_find_conversation_via_phone_number_only() -> None:
    """
    Should find conversation for contact with phone number only.
    """
    dfs = ica.get_dataframes(contact_name="Daniel Brightingale")
    assert len(dfs.messages) > 0


def test_find_conversation_via_email_address_only() -> None:
    """
    Should find conversation for contact with email address only.
    """
    dfs = ica.get_dataframes(contact_name="Thomas Riverstone")
    assert len(dfs.messages) > 0


def test_has_contact_info_but_no_conversation() -> None:
    """
    Should raise a ConversationNotFoundError if contact has info but no
    conversation.
    """
    with pytest.raises(ica.ConversationNotFoundError):
        ica.get_dataframes(contact_name="Evelyn Oakhaven")


def test_missing_contact_info() -> None:
    """
    Should raise a ContactNotFoundError if contact exists but has no contact
    info.
    """
    with pytest.raises(ica.ContactNotFoundError):
        ica.get_dataframes(contact_name="Matthew Whisperton")


def test_contact_not_found_error() -> None:
    """Should raise a ContactNotFoundError when a contact is not found."""
    with pytest.raises(ica.ContactNotFoundError):
        ica.get_dataframes(contact_name="Imaginary Person")
