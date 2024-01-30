#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import unittest

from nose2.tools.decorators import with_setup, with_teardown

import ica
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
def test_missing_phone_number() -> None:
    """
    should raise a ContactNotFoundError if contact exists but has no phone
    number on record
    """
    with case.assertRaises(ica.ContactNotFoundError):
        ica.get_dataframes(contact_name="Matthew Whisperton")


@with_setup(set_up)
@with_teardown(tear_down)
def test_contact_not_found_error() -> None:
    """should raise a ContactNotFoundError when a contact is not found"""
    with case.assertRaises(ica.ContactNotFoundError):
        ica.get_dataframes(contact_name="Imaginary Person")
