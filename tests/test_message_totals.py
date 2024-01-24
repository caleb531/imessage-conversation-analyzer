#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import unittest

import ica

case = unittest.TestCase()


def test_message_count() -> None:
    dfs = ica.get_dataframes(contact_name="John")
