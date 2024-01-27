#!/usr/bin/env python3
"""test the mocking of the database"""

import glob
import sqlite3
import unittest

from nose2.tools.decorators import with_setup, with_teardown

import ica.contact as contact
import ica.core as core
from tests import (
    mock_chats_db_path,
    mock_contacts_db_glob,
    mock_contacts_db_path,
    set_up,
    tear_down,
)

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
def test_db_paths() -> None:
    """should mock paths to databases"""
    case.assertEqual(core.DB_PATH, mock_chats_db_path)
    case.assertEqual(contact.DB_GLOB, mock_contacts_db_glob)
    case.assertIn(
        mock_contacts_db_path,
        glob.glob(mock_contacts_db_glob),
        "glob for mock contacts database does not correctly resolve to database path",
    )


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
