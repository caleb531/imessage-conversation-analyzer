#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import ica


def test_decode_attributedbody() -> None:
    """Should properly decode message contents encoded in attributedBody."""
    dfs = ica.get_dataframes(contact_name="Thomas Riverstone")
    assert dfs.messages.iloc[-1]["text"] == "Loved “Same here! 🤣 Catch you later!”"
