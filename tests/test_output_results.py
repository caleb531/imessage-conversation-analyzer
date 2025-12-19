#!/usr/bin/env python3
"""test the output_results function"""

import csv
from contextlib import redirect_stdout
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

import duckdb
import openpyxl
import pytest

import ica
from tests.utils import temp_ica_dir


@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    return [
        {"first_name": "Steven", "last_name": "Spielberg", "age": 75},
        {"first_name": "Wes", "last_name": "Anderson", "age": 52},
    ]


def test_output_results_text(sample_data: list[dict[str, Any]]) -> None:
    """Should print data as a text table."""
    with redirect_stdout(StringIO()) as stdout:
        ica.output_results(sample_data)
        output = stdout.getvalue()
        # Check headers (Title Cased)
        assert "First Name" in output
        assert "Last Name" in output
        assert "Age" in output
        # Check data
        assert "Steven" in output
        assert "Spielberg" in output
        assert "75" in output


def test_output_results_markdown(sample_data: list[dict[str, Any]]) -> None:
    """Should print data as a markdown table."""
    with redirect_stdout(StringIO()) as stdout:
        ica.output_results(sample_data, format="markdown")
        output = stdout.getvalue()
        output_nospaces = output.replace(" ", "")
        assert "|FirstName|LastName|Age|" in output_nospaces
        assert "|Steven|Spielberg|75|" in output_nospaces


def test_output_results_csv(sample_data: list[dict[str, Any]]) -> None:
    """Should print data as CSV."""
    with redirect_stdout(StringIO()) as stdout:
        ica.output_results(sample_data, format="csv")
        output = stdout.getvalue()
        reader = csv.reader(StringIO(output))
        rows = list(reader)
        assert rows[0] == ["First Name", "Last Name", "Age"]
        assert rows[1] == ["Steven", "Spielberg", "75"]


def test_output_results_excel(sample_data: list[dict[str, Any]]) -> None:
    """Should return Excel bytes."""
    output = BytesIO()
    ica.output_results(sample_data, format="excel", output=output)
    output.seek(0)
    wb = openpyxl.load_workbook(output)
    ws = wb.active
    rows = list(ws.values)
    assert rows[0] == ("First Name", "Last Name", "Age")
    assert rows[1] == ("Steven", "Spielberg", 75)


def test_output_results_duckdb_relation() -> None:
    """Should handle DuckDB relation input."""
    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE people (first_name VARCHAR, last_name VARCHAR)")
    con.execute("INSERT INTO people VALUES ('Martin', 'Scorsese')")
    rel = con.table("people")

    with redirect_stdout(StringIO()) as stdout:
        ica.output_results(rel)
        output = stdout.getvalue()
        assert "First Name" in output
        assert "Last Name" in output
        assert "Martin" in output
        assert "Scorsese" in output


def test_output_results_file(sample_data: list[dict[str, Any]]) -> None:
    """Should write to a file."""
    output_file = Path(f"{temp_ica_dir}/output.csv")
    ica.output_results(sample_data, output=str(output_file))
    assert output_file.exists()
    content = output_file.read_text()
    assert "First Name,Last Name,Age" in content


def test_output_results_invalid_format(sample_data: list[dict[str, Any]]) -> None:
    """Should raise an error if format is invalid."""
    with pytest.raises(ica.FormatNotSupportedError):
        with redirect_stdout(StringIO()):
            ica.output_results(sample_data, format="abc")


def test_output_results_cannot_infer_format(sample_data: list[dict[str, Any]]) -> None:
    """
    Should fall back to default format if format cannot be inferred from
    output path's file extension.
    """
    output_path = f"{temp_ica_dir}/output.abc"
    with redirect_stdout(StringIO()):
        ica.output_results(
            sample_data,
            output=output_path,
        )
        # Should print to file in default format (text table)
        assert Path(output_path).exists()
        content = Path(output_path).read_text()
        assert "First Name" in content
        assert "Steven" in content
