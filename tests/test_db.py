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
        "glob for mock contact database does not correctly resolve to database path",
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
        chat_message_ids = set(
            row[0]
            for row in cur.execute(
                "SELECT message_id FROM chat_message_join"
            ).fetchall()
        )
        case.assertEqual(chat_message_ids, message_ids)
        attachment_message_ids = set(
            row[0]
            for row in cur.execute(
                "SELECT message_id FROM message_attachment_join"
            ).fetchall()
        )
        case.assertLessEqual(attachment_message_ids, message_ids)


@with_setup(set_up)
@with_teardown(tear_down)
def test_contact_db_foreign_keys() -> None:
    """foreign key associations for mock contact database should be correct"""
    with sqlite3.connect(mock_contacts_db_path) as con:
        cur = con.cursor()
        contact_ids = set(
            row[0] for row in cur.execute("SELECT Z_PK FROM ZABCDRECORD").fetchall()
        )
        phone_contact_ids = set(
            row[0]
            for row in cur.execute("SELECT ZOWNER FROM ZABCDPHONENUMBER").fetchall()
        )
        # Every contact must have at least one phone number on file for this
        # program to look up the conversation
        case.assertGreaterEqual(contact_ids, phone_contact_ids)
        email_contact_ids = set(
            row[0]
            for row in cur.execute("SELECT ZOWNER FROM ZABCDEMAILADDRESS").fetchall()
        )
        # However, not every contact needs to have an email address on file
        case.assertLessEqual(email_contact_ids, contact_ids)
