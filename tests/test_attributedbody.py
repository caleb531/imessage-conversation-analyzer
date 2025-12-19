#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import ica


def test_decode_attributedbody() -> None:
    """Should properly decode message contents encoded in attributedBody."""
    data = ica.get_conversation_data(contact_name="Thomas Riverstone")
    # Get the last message
    last_message = data.messages.order("datetime DESC").limit(1).fetchone()
    assert last_message is not None
    # last_message is a tuple (ROWID, text, datetime, is_reaction, is_from_me)
    # I need to know the index of "text".
    # The projection in core.py is:
    # ROWID, text, datetime, is_reaction, is_from_me
    assert last_message[1] == "Loved “Same here! 🤣 Catch you later!”"
