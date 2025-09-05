#!/usr/bin/env python3
"""global test fixtures and helper methods"""

import contextlib
import inspect
import os
import os.path
import shutil
import tempfile
import unittest
from functools import wraps
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Callable, Generator
from unittest import TestCase
from unittest.mock import patch

from tests.mock_db_utils import create_mock_db

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


class ICATestCase(unittest.TestCase):
    """A base class from which all other ICA test case classes inherit."""

    def setUp(self) -> None:
        """
        Create temporary directory and initialize mock databases for each test.
        """
        # If the user aborts the tests with control-C before all tests complete,
        # it can prevent the teardown code from running, thus causing an error
        # the next time tests are run because the database tables still exist;
        # to fix this, we simply run the teardown logic before running the setup
        # logic (we still run it at the end of every test, as well)
        self.tearDown()
        contacts_db_glob_patcher.start()
        chats_db_path_patcher.start()
        with contextlib.suppress(OSError):
            temp_ica_dir.mkdir(parents=True, exist_ok=True)
        create_mock_db("contacts", mock_contacts_db_path)
        create_mock_db("chats", mock_chats_db_path)

    def tearDown(self) -> None:
        """
        Remove temporary directory and unlink mock databases for each test.
        """
        with contextlib.suppress(OSError):
            shutil.rmtree(temp_ica_dir)
        chats_db_path_patcher.stop()
        contacts_db_glob_patcher.stop()


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


class use_env(object):
    """
    A decorator (can also be used as a context manager) which sets an
    environment variable for only the lifetime of the given code; this utility
    works seamlessly for both functions and generators
    """

    def __init__(self, key: str, value: str) -> None:
        self.key: str = key
        self.value: str = value

    def __enter__(self) -> None:
        self.orig_value: str = os.environ.get(self.key, "")
        os.environ[self.key] = self.value

    def __exit__(self, type: type, value: Exception, traceback: Any) -> None:
        os.environ[self.key] = self.orig_value

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def function_wrapper(*args: Any, **kwargs: Any) -> Any:
            with self:
                return func(*args, **kwargs)

        @wraps(func)
        def generator_wrapper(*args: Any, **kwargs: Any) -> Generator[Any, None, Any]:
            with self:
                return (yield from func(*args, **kwargs))

        if inspect.isgeneratorfunction(func):
            return generator_wrapper
        else:
            return function_wrapper
