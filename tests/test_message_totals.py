#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import unittest

from nose2.tools.decorators import with_setup, with_teardown

import ica
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
def test_message_count() -> None:
    dfs = ica.get_dataframes(contact_name="Jane Doe")
