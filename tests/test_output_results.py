#!/usr/bin/env python3
"""test the message_totals built-in analyzer"""

import itertools
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pandas as pd
from nose2.tools import params

import ica
from ica import assign_lambda
from ica.core import prepare_df_for_output
from tests import set_up, tear_down, temp_ica_dir

# A series of tuples representing the output types; the first element of each
# type is the format name, and the second element is the file extension
output_types = (
    (None, "txt", "read_table"),
    ("csv", "csv", "read_csv"),
    ("markdown", "md", "read_table"),
)

test_cases = {
    "default_index": pd.DataFrame(
        {
            "first": ["Steven", "Wes", "Martin"],
            "last": ["Spielberg", "Anderson", "Scorsese"],
        }
    ),
    "labels_in_index": pd.DataFrame(
        {
            "metric": ["Messages", "Reactions", "Attachments"],
            "total": [987, 654, 321],
        },
    ).set_index("metric"),
    "date_index": pd.DataFrame(
        {
            "date": ["2024-01-26", "2024-01-27", "2024-01-28"],
            "total": [12, 45, 56],
        },
    )
    .assign(date=assign_lambda(lambda df: pd.to_datetime(df["date"])))
    .set_index("date"),
}


class TestOutputResults(unittest.TestCase):

    def setUp(self) -> None:
        set_up()

    def tearDown(self) -> None:
        tear_down()

    @params(*itertools.product(test_cases.items(), output_types))
    def test_output_results(
        self,
        test_case: tuple[str, pd.DataFrame],
        output_type: tuple[str, str, str],
    ) -> None:
        """should output a DataFrame under various cases"""
        test_name, df = test_case
        format, ext, df_read_method_name = output_type
        with redirect_stdout(StringIO()) as out:
            ica.output_results(df, format=format)
            self.assertEqual(
                out.getvalue().rstrip(),
                Path(f"tests/data/output/{ext}/output_results_{test_name}.{ext}")
                .read_text()
                .rstrip(),
            )

    @params(
        *itertools.product(
            test_cases.items(),
            # Exclude 'txt' and 'markdown', and add 'excel' to the list of
            # output formats to test
            output_types[1:-1] + (("excel", "xlsx", "read_excel"),),
        )
    )
    def test_output_results_file(
        self,
        test_case: tuple[str, pd.DataFrame],
        output_type: tuple[str, str, str],
    ) -> None:
        """should print a DataFrame to stdout"""
        test_name, df = test_case
        format, ext, df_read_method_name = output_type
        output_path = f"{temp_ica_dir}/{test_name}_{format}.{ext}"
        ica.output_results(
            df,
            format=format,
            output=output_path,
        )
        expected_df = prepare_df_for_output(df.reset_index())
        df_read_method = getattr(pd, df_read_method_name)
        actual_df: pd.DataFrame = df_read_method(output_path)
        actual_df.reset_index()
        actual_df.index += 1
        expected_df
        # print("Actual:\n", actual_df)
        # print("Expected:\n", expected_df)
        # self.assertTrue(
        #     actual_df.equals(expected_df),
        #     f"Dataframes do not match: {actual_df.compare(expected_df)}",
        # )
