#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import itertools
from contextlib import redirect_stdout
from enum import Enum
from io import BytesIO, StringIO
from pathlib import Path
from typing import Union

import pandas as pd
from nose2.tools import params

import ica
from ica import assign_lambda
from ica.core import prepare_df_for_output
from tests import ICATestCase, StdoutMockWithBuffer, temp_ica_dir


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
        .assign(date=assign_lambda(lambda df: pd.to_datetime(df["date"])))
        .set_index("date"),
        IndexType.USE_CUSTOM_INDEX,
    ),
)


class TestOutputResults(ICATestCase):

    @params(
        *itertools.product(
            test_cases,
            (
                (None, "txt", "read_table"),
                ("csv", "csv", "read_csv"),
                ("markdown", "md", "read_table"),
            ),
        )
    )
    def test_output_results(
        self,
        test_case: tuple[str, pd.DataFrame, IndexType],
        output_type: tuple[str, str, str],
    ) -> None:
        """should print a dataframe to stdout"""
        test_name, df, use_default_index = test_case
        format, ext, df_read_method_name = output_type
        with redirect_stdout(StringIO()) as stdout:
            ica.output_results(df, format=format)
            self.assertEqual(
                stdout.getvalue(),
                Path(
                    f"tests/data/output/{ext}/output_results_{test_name}.{ext}"
                ).read_text(),
            )

    @params(
        *itertools.product(
            test_cases,
            ("excel",),
        )
    )
    def test_output_results_bytes(
        self,
        test_case: tuple[str, pd.DataFrame, IndexType],
        format: Union[str, None],
    ) -> None:
        """
        should print the dataframe to stdout as binary Excel data
        """
        test_name, df, use_default_index = test_case
        with redirect_stdout(StdoutMockWithBuffer()) as stdout:
            ica.output_results(
                df,
                format=format,
            )
            self.assertEqual(stdout.getvalue(), "")
            expected_df = prepare_df_for_output(df)
            actual_df = prepare_df_for_output(
                pd.read_excel(
                    stdout.buffer,
                    index_col=None if use_default_index.value else 0,
                )
            )
            self.assertEqual(
                expected_df.to_dict(orient="index"),
                actual_df.to_dict(orient="index"),
            )

    @params(
        *itertools.product(
            test_cases,
            (
                (None, "csv"),
                ("csv", "csv"),
                (None, "md"),
                ("markdown", "md"),
            ),
        )
    )
    def test_output_results_file_plaintext(
        self,
        test_case: tuple[str, pd.DataFrame, IndexType],
        output_type: tuple[str, str],
    ) -> None:
        """should write a DataFrame to a plain-text file"""
        test_name, df, use_default_index = test_case
        format, ext = output_type
        output_path = f"{temp_ica_dir}/{test_name}_{format}.{ext}"
        ica.output_results(
            df,
            format=format,
            output=output_path,
        )
        self.assertEqual(
            Path(output_path).read_text() + "\n",
            Path(
                f"tests/data/output/{ext}/output_results_{test_name}.{ext}"
            ).read_text(),
        )

    @params(
        *itertools.product(
            test_cases,
            (
                ("excel", "xlsx"),
                (None, "xlsx"),
            ),
        )
    )
    def test_output_results_file_binary(
        self,
        test_case: tuple[str, pd.DataFrame, IndexType],
        output_type: tuple[str, str],
    ) -> None:
        """should write a DataFrame to a binary file (i.e. Excel)"""
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
        self.assertEqual(
            actual_df.to_dict(orient="index"),
            expected_df.to_dict(orient="index"),
        )

    @params(
        *itertools.product(
            test_cases,
            (
                (None, "txt"),
                ("csv", "csv"),
                ("markdown", "md"),
            ),
        )
    )
    def test_output_results_string_buffer(
        self,
        test_case: tuple[str, pd.DataFrame, IndexType],
        output_type: tuple[str, str],
    ) -> None:
        """
        should write a dataframe to an explicitly-passed StringIO buffer, but
        not print to stdout
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
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(
                out.getvalue() + "\n",
                Path(
                    f"tests/data/output/{ext}/output_results_{test_name}.{ext}"
                ).read_text(),
            )

    def test_output_results_bytes_buffer(self) -> None:
        """
        should write a dataframe to an explicitly-passed BytesIO buffer, but not
        print to stdout
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
            self.assertEqual(stdout.getvalue(), "")
            expected_df = prepare_df_for_output(df)
            actual_df = prepare_df_for_output(pd.read_excel(out))
            self.assertEqual(
                expected_df.to_dict(orient="index"),
                actual_df.to_dict(orient="index"),
            )

    def test_output_results_invalid_format(self) -> None:
        """should raise an error if format is invalid"""
        test_name, df, use_default_index = test_cases[0]
        with self.assertRaises(ica.FormatNotSupportedError):
            with redirect_stdout(StringIO()):
                ica.output_results(df, format="abc")

    def test_output_results_cannot_infer_format(self) -> None:
        """
        should fall back to default format if format cannot be inferred from
        output path's file extension
        """
        test_name, df, use_default_index = test_cases[0]
        output_path = f"{temp_ica_dir}/output.abc"
        ica.output_results(
            df,
            output=output_path,
        )
        self.assertEqual(
            Path(output_path).read_text() + "\n",
            Path(f"tests/data/output/txt/output_results_{test_name}.txt").read_text(),
        )

    def test_output_results_empty_output_string(self) -> None:
        """
        should print to stdout using default format if output is an empty string
        """
        test_name, df, use_default_index = test_cases[0]
        with redirect_stdout(StringIO()) as stdout:
            ica.output_results(
                df,
                output="",
            )
            self.assertEqual(
                stdout.getvalue(),
                Path(
                    f"tests/data/output/txt/output_results_{test_name}.txt"
                ).read_text(),
            )
