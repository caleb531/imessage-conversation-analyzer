#!/usr/bin/env python3
"""test the participants dataframe"""

import ica


def test_participants_dataframe() -> None:
    """
    Should return a dataframe containing the participants in the conversation
    (besides you / the host user)
    """
    dfs = ica.get_dataframes(contacts=["Daniel Brightingale", "Jane Fernbrook"])
    participants = dfs.participants

    assert len(participants) == 2

    # Sort by first name to ensure consistent order for assertions
    participants = participants.sort_values("first_name").reset_index(drop=True)

    assert participants.iloc[0]["first_name"] == "Daniel"
    assert participants.iloc[0]["last_name"] == "Brightingale"
    assert "+12123456789" in participants.iloc[0]["phone_numbers"]
    assert len(participants.iloc[0]["email_addresses"]) == 0

    assert participants.iloc[1]["first_name"] == "Jane"
    assert participants.iloc[1]["last_name"] == "Fernbrook"
    assert "+12234567890" in participants.iloc[1]["phone_numbers"]
    assert "+12345678901" in participants.iloc[1]["phone_numbers"]
    assert "jane.fernbrook@example.com" in participants.iloc[1]["email_addresses"]
