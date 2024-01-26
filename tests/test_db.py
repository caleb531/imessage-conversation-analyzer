#!/usr/bin/env python3
"""test the mocking of the database"""

import unittest

from nose2.tools.decorators import with_setup, with_teardown

import ica.core
from tests import mock_chats_db_path, set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
def test_db_path() -> None:
    """should mock path to database"""
    case.assertEqual(ica.core.DB_PATH, mock_chats_db_path)
