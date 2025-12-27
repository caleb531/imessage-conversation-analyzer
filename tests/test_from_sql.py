from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest

import ica.analyzers.from_sql as from_sql


@patch(
    "sys.argv",
    [
        from_sql.__file__,
        "SELECT count(*) as total_messages FROM messages",
        "-c",
        "Jane Fernbrook",
    ],
)
def test_from_sql_success() -> None:
    """
    Should execute a valid SQL query and output the results.
    """

    out = StringIO()
    with (
        redirect_stdout(out),
    ):
        from_sql.main()

        assert out.getvalue() == (
            Path("tests/data/output/txt/output_results_from_sql.txt").read_text()
        )


@patch(
    "sys.argv",
    [
        from_sql.__file__,
        "SELECT count(*) as FROM messages",
        "-c",
        "Jane Fernbrook",
    ],
)
def test_from_sql_error() -> None:
    """
    Should raise an error for an invalid SQL query.
    """

    out = StringIO()
    with redirect_stdout(out), pytest.raises(duckdb.ParserException):
        from_sql.main()
