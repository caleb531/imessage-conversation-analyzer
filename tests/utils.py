#!/usr/bin/env python3
"""global test fixtures and helper methods"""

import tempfile
from io import BytesIO, StringIO
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

# Disable maximum length of test diff output for all tests (source:
# <https://stackoverflow.com/a/23617918/560642>)
TestCase.maxDiff = None

# When running tests, point to mock sqlite3 database instead of the default
# macOS chat.db under ~/Library
temp_ica_dir = Path(tempfile.gettempdir()) / "ica"

mock_contacts_db_glob = temp_ica_dir / "*.abcddb"
mock_contacts_db_path = mock_contacts_db_glob.with_name("addressbook.abcddb")
contacts_db_glob_patcher = patch("ica.contact.DB_GLOB", mock_contacts_db_glob)

mock_chats_db_path = temp_ica_dir / "chat.db"
chats_db_path_patcher = patch("ica.core.DB_PATH", mock_chats_db_path)


class StdoutMockWithBuffer(StringIO):
    """
    A mock class for standard output that provides both text and binary buffers.

    The sys.stdout.buffer object is a readonly attribute, and not even
    unittest.mock.patch is able to override it; however, we can subclass
    StringIO() and add a 'buffer' object pointing to a BytesIO() object, then
    pass an instance of this subclass to the stdlib contextlib.redirect_stdout
    context manager without issue.
    #"""

    def __init__(self, initial_value: str = "", newline: str = "\n") -> None:
        super().__init__(initial_value, newline)
        object.__setattr__(self, "buffer", BytesIO())
