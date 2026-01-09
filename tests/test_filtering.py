#!/usr/bin/env python3
"""test the ability to filter analyzer results by date and person"""

import pandas as pd
import pytest

import ica


def test_from_date() -> None:
    """
    Should filter the results to those sent at or after the specified date.
    """
    dfs = ica.get_dataframes(
        contacts=["Jane Fernbrook"],
        timezone="UTC",
        from_date="2024-01-11",
    )
    expected_dates = [
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
        "2024-01-17",
        "2024-01-19",
    ]
    unique_dates = sorted(dfs.messages["datetime"].dt.floor("D").unique())
    assert unique_dates == [pd.Timestamp(date, tz="UTC") for date in expected_dates]


def test_to_date() -> None:
    """
    Should filter the results to those sent before the specified date.
    """
    dfs = ica.get_dataframes(
        contacts=["Jane Fernbrook"],
        timezone="UTC",
        to_date="2024-01-17",
    )
    expected_dates = [
        "2024-01-07",
        "2024-01-08",
        "2024-01-09",
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
    ]
    unique_dates = sorted(dfs.messages["datetime"].dt.floor("D").unique())
    assert unique_dates == [pd.Timestamp(date, tz="UTC") for date in expected_dates]


def test_date_range() -> None:
    """
    Should filter the results to those sent between the specified dates.
    """
    dfs = ica.get_dataframes(
        contacts=["Jane Fernbrook"],
        timezone="UTC",
        from_date="2024-01-11",
        to_date="2024-01-17",
    )
    expected_dates = [
        "2024-01-11",
        "2024-01-14",
        "2024-01-16",
    ]
    unique_dates = sorted(dfs.messages["datetime"].dt.floor("D").unique())
    assert unique_dates == [pd.Timestamp(date, tz="UTC") for date in expected_dates]


def test_invalid_date_range() -> None:
    """
    Should filter the results to those sent between the specified dates.
    """
    with pytest.raises(ica.DateRangeInvalidError):
        ica.get_dataframes(
            contacts=["Jane Fernbrook"],
            timezone="UTC",
            from_date="2024-01-17",
            to_date="2024-01-11",
        )


def test_from_person_me() -> None:
    """
    Should filter the results to those sent by the person running the
    command.
    """
    dfs = ica.get_dataframes(
        contacts=["Thomas Riverstone"],
        from_people=["me"],
    )
    assert len(dfs.messages) == 12
    assert dfs.messages["sender_display_name"].unique().tolist() == ["Me"]

    assert dfs.messages["is_from_me"].all(), (
        "Found messages with is_from_me=False in the filtered dataframe"
    )


def test_from_person_name() -> None:
    """
    Should filter the results to those sent by the specified contact name.
    """
    dfs = ica.get_dataframes(
        contacts=["Thomas Riverstone"],
        from_people=["Thomas"],
    )
    assert len(dfs.messages) == 11
    assert dfs.messages["sender_display_name"].unique().tolist() == ["Thomas"]

    assert not dfs.messages["is_from_me"].any(), (
        "Found messages with is_from_me=True in the filtered dataframe"
    )


def test_from_person_fullname() -> None:
    """
    Should filter the results to those sent by the specified contact full name.
    """
    dfs = ica.get_dataframes(
        contacts=["Thomas Riverstone"],
        from_people=["Thomas Riverstone"],
    )
    assert len(dfs.messages) == 11
    assert dfs.messages["sender_display_name"].unique().tolist() == ["Thomas"]

    assert not dfs.messages["is_from_me"].any(), (
        "Found messages with is_from_me=True in the filtered dataframe"
    )


def test_from_person_email() -> None:
    """
    Should filter the results to those sent by the specified contact identifier.
    """
    dfs = ica.get_dataframes(
        contacts=["Thomas Riverstone"],
        from_people=["thomas.riverstone@example.com"],
    )
    assert len(dfs.messages) == 11
    assert dfs.messages["sender_display_name"].unique().tolist() == ["Thomas"]
    assert not dfs.messages["is_from_me"].any(), (
        "Found messages with is_from_me=True in the filtered dataframe"
    )


def test_from_person_all() -> None:
    """
    Should filter the results to those sent by either participant (i.e. no
    filtering is applied).
    """
    dfs = ica.get_dataframes(
        contacts=["Thomas Riverstone"],
        from_people=["all"],
    )
    assert len(dfs.messages) == 23

    senders = dfs.messages["sender_display_name"].unique().tolist()
    assert "Thomas" in senders
    assert "Me" in senders

    assert dfs.messages["is_from_me"].any(), (
        "Expected messages from me to be included with --from-person all"
    )


def test_from_person_not_found() -> None:
    """
    Should raise ContactNotFoundError for invalid name.
    """
    with pytest.raises(ica.ContactNotFoundError):
        ica.get_dataframes(contacts=["Thomas Riverstone"], from_people=["Bad Name"])
