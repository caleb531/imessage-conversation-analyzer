#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import ica
from tests import ICATestCase


class TestAttributedbody(ICATestCase):

    def test_decode_attributedbody(self) -> None:
        """should properly decode message contents encoded in attributedBody"""
        dfs = ica.get_dataframes(contact_name="Thomas Riverstone")
        self.assertEqual(
            dfs.messages.iloc[-1]["text"], "Loved “Same here! 🤣 Catch you later!”"
        )
