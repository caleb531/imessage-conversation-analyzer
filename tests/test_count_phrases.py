#!/usr/bin/env python3
"""test the count_phrases built-in analyzer"""

import sys
from unittest.mock import MagicMock, patch

import polars as pl

import ica.analyzers.count_phrases as count_phrases


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "-c", "Thomas Riverstone", "reminds me"],
)
def test_single_phrase(output_results: MagicMock) -> None:
    """Should count the number of occurrences of a single phrase."""
    count_phrases.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    phrase = sys.argv[-1]
    assert df.filter(pl.col("phrase") == phrase)["count"].item() == 2


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "-c", "Thomas Riverstone", "hey", "reminds me"],
)
def test_multiple_phrases(output_results: MagicMock) -> None:
    """Should count the number of occurrences of multiple phrases."""
    count_phrases.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    phrases = sys.argv[-2:]
    assert df.filter(pl.col("phrase") == phrases[0])["count"].item() == 2
    assert df.filter(pl.col("phrase") == phrases[1])["count"].item() == 2


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "-c", "Thomas Riverstone", "🤣", "😅"],
)
def test_emoji(output_results: MagicMock) -> None:
    """Should count the number of occurrences of the specified emoji."""
    count_phrases.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    phrases = sys.argv[-2:]
    assert df.filter(pl.col("phrase") == phrases[0])["count"].item() == 2
    assert df.filter(pl.col("phrase") == phrases[0])["count_from_me"].item() == 1
    assert df.filter(pl.col("phrase") == phrases[0])["count_from_them"].item() == 1
    assert df.filter(pl.col("phrase") == phrases[1])["count"].item() == 1
    assert df.filter(pl.col("phrase") == phrases[1])["count_from_me"].item() == 0
    assert df.filter(pl.col("phrase") == phrases[1])["count_from_them"].item() == 1


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "-c", "Jane Fernbrook", " "],
)
def test_whitespace(output_results: MagicMock) -> None:
    """Should count the number of occurrences of a space character."""
    count_phrases.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    phrase = sys.argv[-1]
    assert df.filter(pl.col("phrase") == phrase)["count"].item() == 90
    assert df.filter(pl.col("phrase") == phrase)["count_from_me"].item() == 43
    assert df.filter(pl.col("phrase") == phrase)["count_from_them"].item() == 47


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "-c", "Thomas Riverstone", "!"],
)
def test_special_characters(output_results: MagicMock) -> None:
    """Should count the number of occurrences of a special character."""
    count_phrases.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    phrase = sys.argv[-1]
    assert df.filter(pl.col("phrase") == phrase)["count"].item() == 10
    assert df.filter(pl.col("phrase") == phrase)["count_from_me"].item() == 5
    assert df.filter(pl.col("phrase") == phrase)["count_from_them"].item() == 5


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "-c", "Thomas Riverstone", "--use-regex", "🤣|😅"],
)
def test_regex(output_results: MagicMock) -> None:
    """
    Should count the number of occurrences of strings matching a regular
    expression.
    """
    count_phrases.main()
    df: pl.DataFrame = output_results.call_args[0][0]
    phrase = sys.argv[-1]
    assert df.filter(pl.col("phrase") == phrase)["count"].item() == 3
