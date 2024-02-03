#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""


import ica
from tests import ICATestCase


class TestContact(ICATestCase):

    def test_find_conversation_via_phone_number_only(self) -> None:
        """
        should find conversation for contact with phone number only
        """
        dfs = ica.get_dataframes(contact_name="Daniel Brightingale")
        self.assertGreater(len(dfs.messages), 0)

    def test_find_conversation_via_email_address_only(self) -> None:
        """
        should find conversation for contact with email address only
        """
        dfs = ica.get_dataframes(contact_name="Thomas Riverstone")
        self.assertGreater(len(dfs.messages), 0)

    def test_has_contact_info_but_no_conversation(self) -> None:
        """
        should raise a ConversationNotFoundError if contact has info but no
        conversation
        """
        with self.assertRaises(ica.ConversationNotFoundError):
            ica.get_dataframes(contact_name="Evelyn Oakhaven")

    def test_missing_contact_info(self) -> None:
        """
        should raise a ContactNotFoundError if contact exists but has no contact
        info
        """
        with self.assertRaises(ica.ContactNotFoundError):
            ica.get_dataframes(contact_name="Matthew Whisperton")

    def test_contact_not_found_error(self) -> None:
        """should raise a ContactNotFoundError when a contact is not found"""
        with self.assertRaises(ica.ContactNotFoundError):
            ica.get_dataframes(contact_name="Imaginary Person")
