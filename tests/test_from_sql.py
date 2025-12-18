from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

import pandas as pd

import ica.analyzers.from_sql as from_sql
from ica.core import DataFrameNamespace
from tests.utils import ICATestCase


class TestFromSQL(ICATestCase):
    """
    Test cases for the from_sql analyzer.
    """

    def setUp(self) -> None:
        super().setUp()
        # Create sample dataframes for testing
        self.messages_df = pd.DataFrame(
            {
                "ROWID": [1, 2],
                "text": ["Hello", "World"],
                "is_from_me": [True, False],
            }
        )
        self.attachments_df = pd.DataFrame(
            {
                "ROWID": [1],
                "filename": ["image.png"],
            }
        )
        self.dfs = DataFrameNamespace(
            messages=self.messages_df,
            attachments=self.attachments_df,
        )

    @patch("ica.get_dataframes")
    def test_from_sql_success(self, mock_get_dataframes: MagicMock) -> None:
        """
        Should execute a valid SQL query and output the results.
        """
        mock_get_dataframes.return_value = self.dfs
        query = "SELECT * FROM messages WHERE is_from_me = 1"

        out = StringIO()
        with (
            redirect_stdout(out),
            patch(
                "sys.argv",
                [from_sql.__file__, "-c", "Jane Doe", query],
            ),
        ):
            from_sql.main()

        output = out.getvalue()
        self.assertIn("Rowid", output)
        self.assertIn("Text", output)
        self.assertIn("Hello", output)
        self.assertNotIn("World", output)

    @patch("ica.get_dataframes")
    def test_from_sql_error(self, mock_get_dataframes: MagicMock) -> None:
        """
        Should print an error message to stderr if the query fails.
        """
        mock_get_dataframes.return_value = self.dfs
        query = "SELECT * FROM non_existent_table"

        out = StringIO()
        err = StringIO()
        with (
            redirect_stdout(out),
            redirect_stderr(err),
            patch(
                "sys.argv",
                [from_sql.__file__, "-c", "Jane Doe", query],
            ),
        ):
            from_sql.main()

        self.assertIn("Error executing query", err.getvalue())
        self.assertIn("no such table: non_existent_table", err.getvalue())
