#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import itertools
import locale
from contextlib import redirect_stdout
from enum import Enum
from io import BytesIO, StringIO
from pathlib import Path
from typing import Optional

import pandas as pd
import pytest

import ica
from ica.core import prepare_df_for_output
from tests.utils import StdoutMockWithBuffer, temp_ica_dir


class IndexType(Enum):
    """
    A boolean enum type indicating whether a DataFrame uses the default
    (auto-incrementing) index versus setting a custom index
    """

    USE_DEFAULT_INDEX = True
    USE_CUSTOM_INDEX = False


test_cases = (
    (
        "default_index",
        pd.DataFrame(
            {
                "first": ["Steven", "Wes", "Martin"],
                "last": ["Spielberg", "Anderson", "Scorsese"],
            }
        ),
        IndexType.USE_DEFAULT_INDEX,
    ),
    (
        "labels_in_index",
        pd.DataFrame(
            {
                "metric": ["Messages", "Reactions", "Attachments"],
                "total": [987, 654, 321],
            },
        ).set_index("metric"),
        IndexType.USE_CUSTOM_INDEX,
    ),
    (
        "date_index",
        pd.DataFrame(
            {
                "date": ["2024-01-26", "2024-01-27", "2024-01-28"],
                "total": [12, 45, 56],
            },
        )
        .assign(date=lambda df: pd.to_datetime(df["date"]))
        .set_index("date"),
        IndexType.USE_CUSTOM_INDEX,
    ),
)


@pytest.mark.parametrize(
    ("test_case", "output_type"),
    list(
        itertools.product(
            test_cases,
            (
                (None, "txt", "read_table"),
                ("csv", "csv", "read_csv"),
                ("markdown", "md", "read_table"),
                ("json", "json", "read_json"),
            ),
        )
    ),
)
def test_output_results(
    test_case: tuple[str, pd.DataFrame, IndexType],
    output_type: tuple[str, str, str],
) -> None:
    """Should print a dataframe to stdout."""
    test_name, df, use_default_index = test_case
    format, ext, df_read_method_name = output_type
    with redirect_stdout(StringIO()) as out:
        ica.output_results(df, format=format)
        assert (
            out.getvalue()
            == Path(
                f"tests/data/output/{ext}/output_results_{test_name}.{ext}"
            ).read_text()
        )


@pytest.mark.parametrize(
    ("test_case", "format"),
    list(itertools.product(test_cases, ("excel",))),
)
def test_output_results_bytes(
    test_case: tuple[str, pd.DataFrame, IndexType],
    format: Optional[str],
) -> None:
    """
    Should print the dataframe to stdout as binary Excel data.
    """
    test_name, df, use_default_index = test_case
    with redirect_stdout(StdoutMockWithBuffer()) as out:
        ica.output_results(
            df,
            format=format,
        )
        assert out.getvalue() == ""
        expected_df = prepare_df_for_output(df)
        actual_df = prepare_df_for_output(
            pd.read_excel(
                out.buffer,
                index_col=None if use_default_index.value else 0,
            )
        )
        assert expected_df.to_dict(orient="index") == actual_df.to_dict(orient="index")


@pytest.mark.parametrize(
    ("test_case", "output_type"),
    list(
        itertools.product(
            test_cases,
            (
                (None, "csv"),
                ("csv", "csv"),
                (None, "md"),
                ("markdown", "md"),
            ),
        )
    ),
)
def test_output_results_file_plaintext(
    test_case: tuple[str, pd.DataFrame, IndexType],
    output_type: tuple[str, str],
) -> None:
    """Should write a DataFrame to a plain-text file."""
    test_name, df, use_default_index = test_case
    format, ext = output_type
    output_path = f"{temp_ica_dir}/{test_name}_{format}.{ext}"
    ica.output_results(
        df,
        format=format,
        output=output_path,
    )
    assert (
        Path(output_path).read_text() + "\n"
        == Path(f"tests/data/output/{ext}/output_results_{test_name}.{ext}").read_text()
    )


@pytest.mark.parametrize(
    ("test_case", "output_type"),
    list(
        itertools.product(
            test_cases,
            (
                ("excel", "xlsx"),
                (None, "xlsx"),
            ),
        )
    ),
)
def test_output_results_file_binary(
    test_case: tuple[str, pd.DataFrame, IndexType],
    output_type: tuple[str, str],
) -> None:
    """Should write a DataFrame to a binary file (i.e. Excel)."""
    test_name, df, use_default_index = test_case
    format, ext = output_type
    output_path = f"{temp_ica_dir}/{test_name}_{format}.{ext}"
    ica.output_results(
        df,
        format=format,
        output=output_path,
    )
    expected_df = prepare_df_for_output(df)
    actual_df: pd.DataFrame = prepare_df_for_output(
        pd.read_excel(
            output_path,
            index_col=None if use_default_index.value else 0,
            parse_dates=True,
            date_format="ISO8601",
        )
    )
    assert actual_df.to_dict(orient="index") == expected_df.to_dict(orient="index")


@pytest.mark.parametrize(
    ("test_case", "output_type"),
    list(
        itertools.product(
            test_cases,
            (
                (None, "txt"),
                ("csv", "csv"),
                ("markdown", "md"),
                ("json", "json"),
            ),
        )
    ),
)
def test_output_results_string_buffer(
    test_case: tuple[str, pd.DataFrame, IndexType],
    output_type: tuple[str, str],
) -> None:
    """
    Should write a dataframe to an explicitly-passed StringIO buffer, but
    not print to stdout.
    """
    test_name, df, use_default_index = test_case
    format, ext = output_type
    out = StringIO()
    with redirect_stdout(StringIO()) as stdout:
        ica.output_results(
            df,
            format=format,
            output=out,
        )
        assert stdout.getvalue() == ""
        assert (
            out.getvalue() + "\n"
            == Path(
                f"tests/data/output/{ext}/output_results_{test_name}.{ext}"
            ).read_text()
        )


def test_output_results_bytes_buffer() -> None:
    """
    Should write a dataframe to an explicitly-passed BytesIO buffer, but not
    print to stdout.
    """
    test_name, df, use_default_index = test_cases[0]
    format = "excel"
    out = BytesIO()
    with redirect_stdout(StringIO()) as stdout:
        ica.output_results(
            df,
            format=format,
            output=out,
        )
        assert stdout.getvalue() == ""
        expected_df = prepare_df_for_output(df)
        actual_df = prepare_df_for_output(pd.read_excel(out))
        assert expected_df.to_dict(orient="index") == actual_df.to_dict(orient="index")


def test_output_results_invalid_format() -> None:
    """Should raise an error if format is invalid."""
    test_name, df, use_default_index = test_cases[0]
    with pytest.raises(ica.FormatNotSupportedError):
        with redirect_stdout(StringIO()):
            ica.output_results(df, format="abc")


def test_output_results_cannot_infer_format() -> None:
    """
    Should fall back to default format if format cannot be inferred from
    output path's file extension.
    """
    test_name, df, use_default_index = test_cases[0]
    output_path = f"{temp_ica_dir}/output.abc"
    ica.output_results(
        df,
        output=output_path,
    )
    assert (
        Path(output_path).read_text() + "\n"
        == Path(f"tests/data/output/txt/output_results_{test_name}.txt").read_text()
    )


def test_output_results_empty_output_string() -> None:
    """
    Should print to stdout using default format if output is an empty string.
    """
    test_name, df, use_default_index = test_cases[0]
    with redirect_stdout(StringIO()) as out:
        ica.output_results(
            df,
            output="",
        )
        assert (
            out.getvalue()
            == Path(f"tests/data/output/txt/output_results_{test_name}.txt").read_text()
        )


def test_output_results_prettified_label_override() -> None:
    """
    Should use the provided label overrides when prettifying header names.
    """
    df = pd.DataFrame(
        {
            "foo_bar": [1, 2, 3],
            "baz_qux": [4, 5, 6],
        }
    )
    with redirect_stdout(StringIO()) as out:
        ica.output_results(
            df,
            prettified_label_overrides={"foo_bar": "Foo Bar (Overridden)"},
        )
        output = out.getvalue()
        assert "Foo Bar (Overridden)" in output
        assert "Baz Qux" in output


def test_output_results_locale_aware_separators() -> None:
    """
    Should use locale-aware thousands separators when printing numbers.
    """
    df = pd.DataFrame(
        {
            "metric": ["Messages", "Reactions"],
            "total": [12345, 6789012],
        }
    ).set_index("metric")

    # Test with German locale (uses periods as thousands separators)
    try:
        locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
    except locale.Error:
        pytest.skip("de_DE.UTF-8 locale not supported")

    with redirect_stdout(StringIO()) as out:
        ica.output_results(df)
        output = out.getvalue()
        assert "12.345" in output
        assert "6.789.012" in output

    # Test with US English locale (uses commas as thousands separators)
    try:
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    except locale.Error:
        pytest.skip("en_US.UTF-8 locale not supported")

    with redirect_stdout(StringIO()) as out:
        ica.output_results(df)
        output = out.getvalue()
        assert "12,345" in output
        assert "6,789,012" in output
