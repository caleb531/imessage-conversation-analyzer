#!/usr/bin/env python3
"""test the mocking of the database"""

import collections
import glob
import sqlite3
from collections.abc import Generator
from typing import Any, Sequence, Union

import ica.contact as contact
import ica.core as core
from tests import (
    ICATestCase,
    mock_chats_db_path,
    mock_contacts_db_glob,
    mock_contacts_db_path,
)


def get_duplicates(items: Union[Sequence[Any], Generator[Any, Any, Any]]) -> list[Any]:
    """return a list of duplicates in the given sequence of items"""
    return [item for item, count in collections.Counter(items).items() if count > 1]


class TestDB(ICATestCase):

    def test_db_paths(self) -> None:
        """should mock paths to databases"""
        self.assertEqual(core.DB_PATH, mock_chats_db_path)
        self.assertEqual(contact.DB_GLOB, mock_contacts_db_glob)
        self.assertIn(
            mock_contacts_db_path,
            glob.glob(mock_contacts_db_glob),
            "glob for mock contact database does not correctly resolve to"
            " database path",
        )

    def test_message_timestamp_uniqueness(self) -> None:
        """timestamps should be unique across all tables in the chat database"""
        with sqlite3.connect(mock_chats_db_path) as con:
            cur = con.cursor()
            self.assertFalse(
                get_duplicates(
                    row[0] for row in cur.execute("SELECT date FROM message")
                ),
                "there are duplicate timestamps in the message table",
            )

    def test_message_id_uniqueness(self) -> None:
        """IDs should be unique across all tables in the chat database"""
        with sqlite3.connect(mock_chats_db_path) as con:
            cur = con.cursor()
            self.assertFalse(
                get_duplicates(
                    row[0] for row in cur.execute("SELECT ROWID FROM message")
                ),
                "there are duplicate IDs in the message table",
            )
            self.assertFalse(
                get_duplicates(
                    row[0] for row in cur.execute("SELECT ROWID FROM chat_message_join")
                ),
                "there are duplicate IDs in the chat_message_join table",
            )
            self.assertFalse(
                get_duplicates(
                    row[0]
                    for row in cur.execute("SELECT ROWID FROM message_attachment_join")
                ),
                "there are duplicate IDs in the attachment_message_join table",
            )

    def test_contact_id_uniqueness(self) -> None:
        """IDs should be unique across all tables in the contact database"""
        with sqlite3.connect(mock_contacts_db_path) as con:
            cur = con.cursor()
            self.assertFalse(
                get_duplicates(
                    row[0] for row in cur.execute("SELECT Z_PK FROM ZABCDRECORD")
                ),
                "there are duplicate IDs in the ZABCDRECORD table",
            )

    def test_chat_db_foreign_keys(self) -> None:
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
            self.assertEqual(chat_message_ids, message_ids)
            attachment_message_ids = set(
                row[0]
                for row in cur.execute(
                    "SELECT message_id FROM message_attachment_join"
                ).fetchall()
            )
            self.assertLessEqual(attachment_message_ids, message_ids)

    def test_contact_db_foreign_keys(self) -> None:
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
            self.assertGreaterEqual(contact_ids, phone_contact_ids)
            email_contact_ids = set(
                row[0]
                for row in cur.execute(
                    "SELECT ZOWNER FROM ZABCDEMAILADDRESS"
                ).fetchall()
            )
            # However, not every contact needs to have an email address on file
            self.assertLessEqual(email_contact_ids, contact_ids)
