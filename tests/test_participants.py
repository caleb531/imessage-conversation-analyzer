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

    # Daniel has 1 identifier, Jane has 1. Total 2 rows.
    assert len(participants) == 2

    # Sort by identifier to ensure consistent order
    participants = participants.sort_values("identifier").reset_index(drop=True)

    # Row 0: Daniel (+12123456789)
    assert participants.iloc[0]["first_name"] == "Daniel"
    assert participants.iloc[0]["last_name"] == "Brightingale"
    assert participants.iloc[0]["identifier"] == "+12123456789"

    # Row 1: Jane (+12234567890)
    assert participants.iloc[1]["first_name"] == "Jane"
    assert participants.iloc[1]["last_name"] == "Fernbrook"
    assert participants.iloc[1]["identifier"] == "+12234567890"
