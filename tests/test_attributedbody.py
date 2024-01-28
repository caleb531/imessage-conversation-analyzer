#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import unittest

from nose2.tools.decorators import with_setup, with_teardown

import ica
from tests import set_up, tear_down

case = unittest.TestCase()


@with_setup(set_up)
@with_teardown(tear_down)
def test_decode_attributedbody() -> None:
    """should properly decode message contents encoded in attributedBody"""
    dfs = ica.get_dataframes(contact_name="James Doe")
    case.assertEqual(
        dfs.messages.iloc[-1]["text"], "Loved “Same here! 🤣 Catch you later!”"
    )
