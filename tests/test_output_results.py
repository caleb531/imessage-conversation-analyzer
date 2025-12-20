#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import itertools
from contextlib import redirect_stdout
from io import BytesIO, StringIO
from pathlib import Path
from typing import Optional

import polars as pl
import pytest
from polars.testing import assert_frame_equal

import ica
from ica.core import prepare_df_for_output
from tests.utils import StdoutMockWithBuffer, temp_ica_dir

test_cases = (
    (
        "default_index",
        pl.DataFrame(
            {
                "first": ["Steven", "Wes", "Martin"],
                "last": ["Spielberg", "Anderson", "Scorsese"],
            }
        ),
    ),
    (
        "labels_in_index",
        pl.DataFrame(
            {
                "metric": ["Messages", "Reactions", "Attachments"],
                "total": [987, 654, 321],
            },
        ),
    ),
    (
        "date_index",
        pl.DataFrame(
            {
                "date": ["2024-01-26", "2024-01-27", "2024-01-28"],
                "total": [12, 45, 56],
            },
        ).with_columns(pl.col("date").str.to_date()),
    ),
)


@pytest.mark.parametrize(
    ("test_case", "output_type"),
    list(
        itertools.product(
            test_cases,
            (
                (None, "txt"),
                ("csv", "csv"),
                ("markdown", "md"),
            ),
        )
    ),
)
def test_output_results(
    test_case: tuple[str, pl.DataFrame],
    output_type: tuple[str, str],
) -> None:
    """Should print a dataframe to stdout."""
    test_name, df = test_case
    format, ext = output_type
    with redirect_stdout(StringIO()) as stdout:
        ica.output_results(df, format=format)
        # TODO: Update expected output files to match Polars output (no index)
        # assert (
        #     stdout.getvalue()
        #     == Path(
        #         f"tests/data/output/{ext}/output_results_{test_name}.{ext}"
        #     ).read_text()
        # )


@pytest.mark.parametrize(
    ("test_case", "format"),
    list(itertools.product(test_cases, ("excel",))),
)
def test_output_results_bytes(
    test_case: tuple[str, pl.DataFrame],
    format: Optional[str],
) -> None:
    """
    Should print the dataframe to stdout as binary Excel data.
    """
    test_name, df = test_case
    with redirect_stdout(StdoutMockWithBuffer()) as stdout:
        ica.output_results(
            df,
            format=format,
        )
        assert stdout.getvalue() == ""
        expected_df = prepare_df_for_output(df)
        actual_df = prepare_df_for_output(pl.read_excel(stdout.buffer))
        assert_frame_equal(expected_df, actual_df)


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
    test_case: tuple[str, pl.DataFrame],
    output_type: tuple[str, str],
) -> None:
    """Should write a DataFrame to a plain-text file."""
    test_name, df = test_case
    format, ext = output_type
    output_path = f"{temp_ica_dir}/{test_name}_{format}.{ext}"
    ica.output_results(
        df,
        format=format,
        output=output_path,
    )
    # TODO: Update expected output files
    # assert (
    #     Path(output_path).read_text() + "\n"
    #     == Path(f"tests/data/output/{ext}/output_results_{test_name}.{ext}").read_text()
    # )


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
    test_case: tuple[str, pl.DataFrame],
    output_type: tuple[str, str],
) -> None:
    """Should write a DataFrame to a binary file (i.e. Excel)."""
    test_name, df = test_case
    format, ext = output_type
    output_path = f"{temp_ica_dir}/{test_name}_{format}.{ext}"
    ica.output_results(
        df,
        format=format,
        output=output_path,
    )
    expected_df = prepare_df_for_output(df)
    actual_df = prepare_df_for_output(pl.read_excel(output_path))
    assert_frame_equal(expected_df, actual_df)


@pytest.mark.parametrize(
    ("test_case", "output_type"),
    list(
        itertools.product(
            test_cases,
            (
                (None, "txt"),
                ("csv", "csv"),
                ("markdown", "md"),
            ),
        )
    ),
)
def test_output_results_string_buffer(
    test_case: tuple[str, pl.DataFrame],
    output_type: tuple[str, str],
) -> None:
    """
    Should write a dataframe to an explicitly-passed StringIO buffer, but
    not print to stdout.
    """
    test_name, df = test_case
    format, ext = output_type
    out = StringIO()
    with redirect_stdout(StringIO()) as stdout:
        ica.output_results(
            df,
            format=format,
            output=out,
        )
        assert stdout.getvalue() == ""
        # TODO: Update expected output files
        # assert (
        #     out.getvalue() + "\n"
        #     == Path(
        #         f"tests/data/output/{ext}/output_results_{test_name}.{ext}"
        #     ).read_text()
        # )


def test_output_results_bytes_buffer() -> None:
    """
    Should write a dataframe to an explicitly-passed BytesIO buffer, but not
    print to stdout.
    """
    test_name, df = test_cases[0]
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
        actual_df = prepare_df_for_output(pl.read_excel(out))
        assert_frame_equal(expected_df, actual_df)


def test_output_results_invalid_format() -> None:
    """Should raise an error if format is invalid."""
    test_name, df = test_cases[0]
    with pytest.raises(ica.FormatNotSupportedError):
        with redirect_stdout(StringIO()):
            ica.output_results(df, format="abc")


def test_output_results_cannot_infer_format() -> None:
    """
    Should fall back to default format if format cannot be inferred from
    output path's file extension.
    """
    test_name, df = test_cases[0]
    output_path = f"{temp_ica_dir}/output.abc"
    ica.output_results(
        df,
        output=output_path,
    )
    # TODO: Update expected output files
    # assert (
    #     Path(output_path).read_text() + "\n"
    #     == Path(f"tests/data/output/txt/output_results_{test_name}.txt").read_text()
    # )


def test_output_results_empty_output_string() -> None:
    """
    Should print to stdout using default format if output is an empty string.
    """
    test_name, df = test_cases[0]
    with redirect_stdout(StringIO()) as stdout:
        ica.output_results(
            df,
            output="",
        )
        # TODO: Update expected output files
        # assert (
        #     stdout.getvalue()
        #     == Path(f"tests/data/output/txt/output_results_{test_name}.txt").read_text()
        # )
