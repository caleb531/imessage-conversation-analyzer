#!/usr/bin/env python3
"""test the count_phrases built-in analyzer"""

import sys
from unittest.mock import MagicMock, patch

import ica.analyzers.count_phrases as count_phrases


def get_count(data: list[dict], phrase: str, key: str = "count") -> int:
    for item in data:
        if item["phrase"] == phrase:
            return item[key]
    return -1


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "-c", "Thomas Riverstone", "reminds me"],
)
def test_single_phrase(output_results: MagicMock) -> None:
    """Should count the number of occurrences of a single phrase."""
    count_phrases.main()
    data = output_results.call_args[0][0]
    phrase = sys.argv[-1]
    assert get_count(data, phrase) == 2


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "-c", "Thomas Riverstone", "hey", "reminds me"],
)
def test_multiple_phrases(output_results: MagicMock) -> None:
    """Should count the number of occurrences of multiple phrases."""
    count_phrases.main()
    data = output_results.call_args[0][0]
    phrases = sys.argv[-2:]
    assert get_count(data, phrases[0]) == 2
    assert get_count(data, phrases[1]) == 2


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "-c", "Thomas Riverstone", "🤣", "😅"],
)
def test_emoji(output_results: MagicMock) -> None:
    """Should count the number of occurrences of the specified emoji."""
    count_phrases.main()
    data = output_results.call_args[0][0]
    phrases = sys.argv[-2:]
    assert get_count(data, phrases[0]) == 2
    assert get_count(data, phrases[0], "count_from_me") == 1
    assert get_count(data, phrases[0], "count_from_them") == 1
    assert get_count(data, phrases[1]) == 1
    assert get_count(data, phrases[1], "count_from_me") == 0
    assert get_count(data, phrases[1], "count_from_them") == 1


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "-c", "Jane Fernbrook", " "],
)
def test_whitespace(output_results: MagicMock) -> None:
    """Should count the number of occurrences of a space character."""
    count_phrases.main()
    data = output_results.call_args[0][0]
    phrase = sys.argv[-1]
    assert get_count(data, phrase) == 90
    assert get_count(data, phrase, "count_from_me") == 43
    assert get_count(data, phrase, "count_from_them") == 47


@patch("ica.output_results")
@patch(
    "sys.argv",
    [count_phrases.__file__, "-c", "Thomas Riverstone", "!"],
)
def test_special_characters(output_results: MagicMock) -> None:
    """Should count the number of occurrences of a special character."""
    count_phrases.main()
    data = output_results.call_args[0][0]
    phrase = sys.argv[-1]
    assert get_count(data, phrase) == 10
    assert get_count(data, phrase, "count_from_me") == 5
    assert get_count(data, phrase, "count_from_them") == 5


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
    data = output_results.call_args[0][0]
    phrase = sys.argv[-1]
    assert get_count(data, phrase) == 3
    assert get_count(data, phrase, "count_from_me") == 1
    assert get_count(data, phrase, "count_from_them") == 2
