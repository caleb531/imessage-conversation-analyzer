#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import unittest

from nose2.tools.decorators import with_setup, with_teardown

import ica
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
def test_has_conversation_via_email_address_only() -> None:
    """
    should not error if contact with conversation is missing phone number but
    has an email address
    """
    dfs = ica.get_dataframes(contact_name="Thomas Riverstone")
    case.assertGreater(len(dfs.messages), 0)


@with_setup(set_up)
@with_teardown(tear_down)
def test_has_contact_info_but_no_conversation() -> None:
    """
    should not error if contact has phone number but no conversation
    """
    dfs = ica.get_dataframes(contact_name="Evelyn Oakhaven")
    case.assertEqual(len(dfs.messages), 0)


@with_setup(set_up)
@with_teardown(tear_down)
def test_missing_contact_info() -> None:
    """
    should raise a ContactNotFoundError if contact exists but has no phone
    number or email address on record
    """
    with case.assertRaises(ica.ContactNotFoundError):
        ica.get_dataframes(contact_name="Matthew Whisperton")


@with_setup(set_up)
@with_teardown(tear_down)
def test_contact_not_found_error() -> None:
    """should raise a ContactNotFoundError when a contact is not found"""
    with case.assertRaises(ica.ContactNotFoundError):
        ica.get_dataframes(contact_name="Imaginary Person")
