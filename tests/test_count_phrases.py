#!/usr/bin/env python3
"""test the count_phrases built-in analyzer"""

import sys
from unittest.mock import MagicMock, patch

import pandas as pd

import ica.analyzers.count_phrases as count_phrases


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "reminds me", "-c", "Thomas Riverstone"],
)
def test_single_phrase(output_results: MagicMock) -> None:
    """Should count the number of occurrences of a single phrase."""
    count_phrases.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    phrase = sys.argv[1]
    assert df.loc[phrase]["count"] == 2


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "hey", "reminds me", "-c", "Thomas Riverstone"],
)
def test_multiple_phrases(output_results: MagicMock) -> None:
    """Should count the number of occurrences of multiple phrases."""
    count_phrases.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    phrases = sys.argv[1:3]
    assert df.loc[phrases[0]]["count"] == 2
    assert df.loc[phrases[1]]["count"] == 2


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "🤣", "😅", "-c", "Thomas Riverstone"],
)
def test_emoji(output_results: MagicMock) -> None:
    """Should count the number of occurrences of the specified emoji."""
    count_phrases.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    phrases = sys.argv[1:3]
    assert df.loc[phrases[0]]["count"] == 2
    assert df.loc[phrases[0]]["count_from_me"] == 1
    assert df.loc[phrases[0]]["count_from_Thomas"] == 1
    assert df.loc[phrases[1]]["count"] == 1
    assert df.loc[phrases[1]]["count_from_me"] == 0
    assert df.loc[phrases[1]]["count_from_Thomas"] == 1


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, " ", "-c", "Jane Fernbrook"],
)
def test_whitespace(output_results: MagicMock) -> None:
    """Should count the number of occurrences of a space character."""
    count_phrases.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    phrase = sys.argv[1]
    assert df.loc[phrase]["count"] == 90
    assert df.loc[phrase]["count_from_me"] == 43
    assert df.loc[phrase]["count_from_Jane"] == 47


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "?", "-c", "Thomas Riverstone"],
)
def test_special_characters(output_results: MagicMock) -> None:
    """Should count the number of occurrences of a special character."""
    count_phrases.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    phrase = sys.argv[1]
    assert df.loc[phrase]["count"] == 9
    assert df.loc[phrase]["count_from_me"] == 2
    assert df.loc[phrase]["count_from_Thomas"] == 7


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "🤣|😅", "-c", "Thomas Riverstone", "--use-regex"],
)
def test_regex(output_results: MagicMock) -> None:
    """
    Should count the number of occurrences of strings matching a regular
    expression.
    """
    count_phrases.main()
    df: pd.DataFrame = output_results.call_args[0][0]
    phrase = sys.argv[1]
    assert df.loc[phrase]["count"] == 3
    assert df.loc[phrase]["count_from_me"] == 1
    assert df.loc[phrase]["count_from_Thomas"] == 2
