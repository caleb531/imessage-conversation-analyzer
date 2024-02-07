#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import itertools
from contextlib import redirect_stdout
from enum import Enum
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
from nose2.tools import params

import ica
from ica import assign_lambda
from ica.core import prepare_df_for_output
from tests import ICATestCase, temp_ica_dir


class IndexType(Enum):

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
            (
                (None, "csv", "read_csv"),
                ("csv", "csv", "read_csv"),
                ("excel", "xlsx", "read_excel"),
                (None, "xlsx", "read_excel"),
            ),
        )
    )
    def test_output_results_file(
        self,
        test_case: tuple[str, pd.DataFrame, IndexType],
        output_type: tuple[str, str, str],
    ) -> None:
        """should write a DataFrame to file"""
        test_name, df, use_default_index = test_case
        format, ext, df_read_method_name = output_type
        output_path = f"{temp_ica_dir}/{test_name}_{format}.{ext}"
        ica.output_results(
            df,
            format=format,
            output=output_path,
        )
        expected_df = prepare_df_for_output(df)
        df_read_method = getattr(pd, df_read_method_name)
        actual_df: pd.DataFrame = df_read_method(
            output_path,
            index_col=None if use_default_index.value else 0,
            parse_dates=True,
            date_format="ISO8601",
        )
        # Use base-1 index if index is the default auto-incrementing index
        # (since that's how prepare_df_for_output will normalize expected_df)
        actual_df.reset_index()
        if use_default_index.value:
            actual_df.index += 1
        self.assertEqual(
            actual_df.to_dict(orient="index"),
            expected_df.to_dict(orient="index"),
        )

    def test_output_results_string_buffer(
        self,
    ) -> None:
        """
        should write a dataframe to an explicitly-passed StringIO buffer, but
        not print to stdout
        """
        test_name, df, use_default_index = test_cases[0]
        format = "csv"
        ext = "csv"
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

    def test_output_results_bytes_buffer(
        self,
    ) -> None:
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

    def test_output_results_invalid_format(
        self,
    ) -> None:
        """should raise an error if format is invalid"""
        test_name, df, use_default_index = test_cases[0]
        with self.assertRaises(ica.FormatNotSupportedError):
            with redirect_stdout(StringIO()):
                ica.output_results(df, format="abc")
