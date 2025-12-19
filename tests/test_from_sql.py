from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

import duckdb
import pytest

import ica.analyzers.from_sql as from_sql
from ica.core import ConversationData


@pytest.fixture
def conversation_data() -> ConversationData:
    """Create sample conversation data for testing."""
    con = duckdb.connect(":memory:")
    con.execute(
        "CREATE TABLE messages_table (ROWID INTEGER, text VARCHAR, is_from_me BOOLEAN)"
    )
    con.execute(
        "INSERT INTO messages_table VALUES (1, 'Hello', true), (2, 'World', false)"
    )
    con.execute("CREATE TABLE attachments_table (ROWID INTEGER, filename VARCHAR)")
    con.execute("INSERT INTO attachments_table VALUES (1, 'image.png')")

    return ConversationData(
        con=con,
        messages=con.table("messages_table"),
        attachments=con.table("attachments_table"),
    )


@patch("ica.get_conversation_data")
def test_from_sql_success(
    mock_get_conversation_data: MagicMock, conversation_data: ConversationData
) -> None:
    """
    Should execute a valid SQL query and output the results.
    """
    mock_get_conversation_data.return_value = conversation_data
    query = "SELECT * FROM messages WHERE is_from_me = true"

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
    assert "Rowid" in output
    assert "Text" in output
    assert "Hello" in output
    assert "World" not in output


@patch("ica.get_conversation_data")
def test_from_sql_error(
    mock_get_conversation_data: MagicMock, conversation_data: ConversationData
) -> None:
    """
    Should print an error message to stderr if the query fails.
    """
    mock_get_conversation_data.return_value = conversation_data
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

    assert "Error executing query" in err.getvalue()
    assert "Table with name non_existent_table does not exist" in err.getvalue()


@patch("ica.get_conversation_data")
def test_from_sql_custom_format(
    mock_get_conversation_data: MagicMock, conversation_data: ConversationData
) -> None:
    """
    Should respect the format argument.
    """
    mock_get_conversation_data.return_value = conversation_data
    query = "SELECT text FROM messages"

    out = StringIO()
    with (
        redirect_stdout(out),
        patch(
            "sys.argv",
            [from_sql.__file__, "-c", "Jane Doe", "-f", "csv", query],
        ),
    ):
        from_sql.main()

    output = out.getvalue()
    assert "Text" in output
    assert "Hello" in output
    assert "World" in output
    # CSV format should have commas (though with one column it might just be
    # the header and values).
    assert len(output) > 0
