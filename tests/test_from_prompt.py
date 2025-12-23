import types
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import ica.analyzers.from_prompt.__main__ as from_prompt
from ica.analyzers.from_prompt.exceptions import (
    EmptyResponseError,
    ResponseMissingSQLError,
)
from tests.utils import temp_ica_dir

API_KEY = "abc"
PROMPT = "test prompt"

# Ensure `Path` is used consistently for file operations
MOCK_SQL_QUERY = (
    Path("tests/data/queries/generated_from_prompt.sql").read_text().strip()
)


def get_mock_completion_response(
    content: str = f"```sql\n{MOCK_SQL_QUERY}\n```",
    include_usage: bool = True,
) -> types.SimpleNamespace:
    """
    Construct a mock object that resembles a response from the OpenAI
    Completions API
    """
    msg = types.SimpleNamespace(content=content)
    choice = types.SimpleNamespace(message=msg)
    if include_usage:
        usage = types.SimpleNamespace(prompt_tokens=10, completion_tokens=2)
    else:
        usage = None
    return types.SimpleNamespace(choices=[choice], usage=usage)


@pytest.fixture
def openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the OPENAI_API_KEY environment variable."""
    monkeypatch.setenv("OPENAI_API_KEY", API_KEY)


@patch(
    "openai.chat.completions.create",
    return_value=get_mock_completion_response(),
)
@patch(
    "sys.argv",
    [from_prompt.__file__, "-c", "Jane Fernbrook", "--api-key", API_KEY, PROMPT],
)
def test_from_prompt_with_usage(
    completions_create: Mock,
    openai_api_key: None,
) -> None:
    """
    Should call the OpenAI API to generate SQL, then run that
    SQL query, printing usage information when available
    """
    out = StringIO()
    with redirect_stdout(out):
        from_prompt.main()
        _, kwargs = completions_create.call_args
        assert kwargs["model"] == from_prompt.MODEL
        assert kwargs["max_tokens"] == 4096
        assert kwargs["messages"][0]["role"] == "system"
        assert kwargs["messages"][1]["role"] == "user"

        assert out.getvalue() == (
            Path("tests/data/output/txt/output_results_from_prompt_with_usage.txt")
            .read_text()
            .replace(r"{MODEL}", from_prompt.MODEL)
        )


@patch(
    "openai.chat.completions.create",
    return_value=get_mock_completion_response(include_usage=False),
)
@patch(
    "sys.argv",
    [from_prompt.__file__, "-c", "Jane Fernbrook", "--api-key", API_KEY, PROMPT],
)
def test_from_prompt_no_usage(
    completions_create: Mock,
    openai_api_key: None,
) -> None:
    """
    Should call the OpenAI API to generate SQL, then run that
    SQL query, informing the user when usage information is unavailable
    """
    out = StringIO()
    with redirect_stdout(out):
        from_prompt.main()
        _, kwargs = completions_create.call_args
        assert kwargs["model"] == from_prompt.MODEL
        assert kwargs["max_tokens"] == 4096
        assert kwargs["messages"][0]["role"] == "system"
        assert kwargs["messages"][1]["role"] == "user"

        assert out.getvalue() == (
            Path("tests/data/output/txt/output_results_from_prompt_no_usage.txt")
            .read_text()
            .replace(r"{MODEL}", from_prompt.MODEL)
        )


@patch(
    "openai.chat.completions.create",
    return_value=get_mock_completion_response(),
)
def test_from_prompt_keep_sql(
    completions_create: Mock,
    openai_api_key: None,
) -> None:
    """
    Should write the generated SQL to disk when the option is passed
    """
    out = StringIO()
    generated_sql_file_name = "generated_from_prompt.sql"
    generated_sql_file_path = f"{temp_ica_dir}/{generated_sql_file_name}"
    with (
        redirect_stdout(out),
        patch(
            "sys.argv",
            [
                from_prompt.__file__,
                "-c",
                "Jane Fernbrook",
                "--api-key",
                API_KEY,
                "--write",
                generated_sql_file_path,
                PROMPT,
            ],
        ),
    ):
        from_prompt.main()
        assert Path(generated_sql_file_path).read_text().strip() == MOCK_SQL_QUERY


@patch(
    "openai.chat.completions.create",
    return_value=get_mock_completion_response(content=""),
)
@patch(
    "sys.argv",
    [from_prompt.__file__, "-c", "Jane Fernbrook", "--api-key", API_KEY, PROMPT],
)
def test_from_prompt_empty_response(
    completions_create: Mock,
    openai_api_key: None,
) -> None:
    """
    Should raise an error if the OpenAI API returns an empty response
    """
    out = StringIO()
    with redirect_stdout(out), pytest.raises(EmptyResponseError):
        from_prompt.main()


@patch(
    "openai.chat.completions.create",
    return_value=get_mock_completion_response(content="Response without SQL"),
)
@patch(
    "sys.argv",
    [from_prompt.__file__, "-c", "Jane Fernbrook", "--api-key", API_KEY, PROMPT],
)
def test_from_prompt_no_sql_in_response(
    completions_create: Mock,
    openai_api_key: None,
) -> None:
    """
    Should raise an error if the OpenAI API returns a response without any
    SQL
    """
    out = StringIO()
    with redirect_stdout(out), pytest.raises(ResponseMissingSQLError):
        from_prompt.main()
