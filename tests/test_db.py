#!/usr/bin/env python3
"""test the mocking of the database"""

import sqlite3
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


@with_setup(set_up)
@with_teardown(tear_down)
def test_chat_db_foreign_keys() -> None:
    """foreign key associations for mock chat database should be correct"""
    with sqlite3.connect(mock_chats_db_path) as con:
        cur = con.cursor()
        message_ids = set(
            row[0] for row in cur.execute("SELECT ROWID FROM message").fetchall()
        )
        joined_message_ids = set(
            row[0]
            for row in cur.execute(
                "SELECT message_id FROM chat_message_join"
            ).fetchall()
        )
        case.assertEqual(joined_message_ids, message_ids)
