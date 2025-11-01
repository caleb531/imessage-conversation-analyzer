#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""
import unittest

import ica
from tests.utils import ICATestCase


class TestAttributedbody(unittest.TestCase):
    """
    Test cases for decoding message contents encoded in the `attributedBody`
    field.
    """

    def test_decode_attributedbody(self) -> None:
        """Should properly decode message contents encoded in attributedBody."""
        dfs = ica.get_dataframes(contact_name="Thomas Riverstone")
        self.assertEqual(
            dfs.messages.iloc[-1]["text"], "Loved “Same here! 🤣 Catch you later!”"
        )
