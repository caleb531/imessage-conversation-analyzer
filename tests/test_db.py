#!/usr/bin/env python3
"""test the mocking of the database"""

import unittest

from nose2.tools.decorators import with_setup, with_teardown

import ica.core
from tests import mock_database, set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
def test_db_path() -> None:
    """should mock path to database"""
    case.assertIn("/var/", ica.core.DB_PATH)


@with_setup(set_up)
@with_teardown(tear_down)
def test_message_row_count() -> None:
    """should populate the correct number of rows into the message table"""
    with mock_database():
        pass
