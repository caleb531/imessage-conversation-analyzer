import types
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import ica.analyzers.from_prompt.__main__ as from_prompt
from ica.analyzers.from_prompt.exceptions import (
    EmptyResponseError,
    ResponseMissingSQLError,
)
from tests.utils import ICATestCase, temp_ica_dir, use_env

API_KEY = "abc"
PROMPT = "test prompt"

# Ensure `Path` is used consistently for file operations
MOCK_SQL_QUERY = (
    Path("tests/data/analyzers/generated_from_prompt.sql").read_text().strip()
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


class TestFromPrompt(ICATestCase):
    """
    Test cases for generating SQL from prompts using the OpenAI API,
    including handling of API responses and generated SQL.
    """

    def setUp(self) -> None:
        self.mock_output_results = patch("ica.output_results").start()
        self.mock_execute_sql_query = patch("ica.execute_sql_query").start()
        self.mock_create_temp_sql_db = patch("ica.create_temp_sql_db").start()
        self.mock_get_dataframes = patch("ica.get_dataframes").start()

        # Setup context manager for create_temp_sql_db
        self.mock_db_con = MagicMock()
        self.mock_create_temp_sql_db.return_value.__enter__.return_value = (
            self.mock_db_con
        )

        # Setup output_results to print the expected table
        def side_effect(*args: Any, **kwargs: Any) -> None:
            print("Metric              Total")
            print("Messages             1200")
            print("Messages From Me      700")
            print("Messages From Them    500")

        self.mock_output_results.side_effect = side_effect

    def tearDown(self) -> None:
        patch.stopall()

    # The openai.OpenAIError raised when we mock the OpenAI API below due to the
    # API_KEY environment variable not being set
    @use_env("OPENAI_API_KEY", API_KEY)
    @patch(
        "openai.chat.completions.create",
        return_value=get_mock_completion_response(),
    )
    @patch(
        "sys.argv",
        [from_prompt.__file__, "-c", "Jane Fernbrook", "--api-key", API_KEY, PROMPT],
    )
    def test_from_prompt_with_usage(self, completions_create: Mock) -> None:
        """
        Should call the OpenAI API to generate SQL, then run that
        SQL query, printing usage information when available
        """
        out = StringIO()
        with redirect_stdout(out):
            from_prompt.main()
            _, kwargs = completions_create.call_args
            self.assertEqual(kwargs["model"], from_prompt.MODEL)
            self.assertEqual(kwargs["max_tokens"], 4096)
            self.assertEqual(kwargs["messages"][0]["role"], "system")
            self.assertEqual(kwargs["messages"][1]["role"], "user")

            # Verify SQL execution
            self.mock_execute_sql_query.assert_called_once_with(
                MOCK_SQL_QUERY, self.mock_db_con
            )
            self.mock_output_results.assert_called_once()

            self.assertEqual(
                out.getvalue(),
                Path("tests/data/output/txt/output_results_from_prompt_with_usage.txt")
                .read_text()
                .replace(r"{MODEL}", from_prompt.MODEL),
            )

    @use_env("OPENAI_API_KEY", API_KEY)
    @patch(
        "openai.chat.completions.create",
        return_value=get_mock_completion_response(include_usage=False),
    )
    @patch(
        "sys.argv",
        [from_prompt.__file__, "-c", "Jane Fernbrook", "--api-key", API_KEY, PROMPT],
    )
    def test_from_prompt_no_usage(self, completions_create: Mock) -> None:
        """
        Should call the OpenAI API to generate SQL, then run that
        SQL query, informing the user when usage information is unavailable
        """
        out = StringIO()
        with redirect_stdout(out):
            from_prompt.main()
            _, kwargs = completions_create.call_args
            self.assertEqual(kwargs["model"], from_prompt.MODEL)
            self.assertEqual(kwargs["max_tokens"], 4096)
            self.assertEqual(kwargs["messages"][0]["role"], "system")
            self.assertEqual(kwargs["messages"][1]["role"], "user")

            # Verify SQL execution
            self.mock_execute_sql_query.assert_called_once_with(
                MOCK_SQL_QUERY, self.mock_db_con
            )

            self.assertEqual(
                out.getvalue(),
                Path("tests/data/output/txt/output_results_from_prompt_no_usage.txt")
                .read_text()
                .replace(r"{MODEL}", from_prompt.MODEL),
            )

    @use_env("OPENAI_API_KEY", API_KEY)
    @patch(
        "openai.chat.completions.create",
        return_value=get_mock_completion_response(),
    )
    def test_from_prompt_keep_sql(self, completions_create: Mock) -> None:
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
            self.assertEqual(
                Path(generated_sql_file_path).read_text().strip(),
                MOCK_SQL_QUERY,
            )

    @use_env("OPENAI_API_KEY", API_KEY)
    @patch(
        "openai.chat.completions.create",
        return_value=get_mock_completion_response(content=""),
    )
    @patch(
        "sys.argv",
        [from_prompt.__file__, "-c", "Jane Fernbrook", "--api-key", API_KEY, PROMPT],
    )
    def test_from_prompt_empty_response(self, completions_create: Mock) -> None:
        """
        Should raise an error if the OpenAI API returns an empty response
        """
        out = StringIO()
        with redirect_stdout(out), self.assertRaises(EmptyResponseError):
            from_prompt.main()

    @use_env("OPENAI_API_KEY", API_KEY)
    @patch(
        "openai.chat.completions.create",
        return_value=get_mock_completion_response(content="Response without SQL"),
    )
    @patch(
        "sys.argv",
        [from_prompt.__file__, "-c", "Jane Fernbrook", "--api-key", API_KEY, PROMPT],
    )
    def test_from_prompt_no_sql_in_response(self, completions_create: Mock) -> None:
        """
        Should raise an error if the OpenAI API returns a response without any
        SQL
        """
        out = StringIO()
        with redirect_stdout(out), self.assertRaises(ResponseMissingSQLError):
            from_prompt.main()

    @use_env("OPENAI_API_KEY", API_KEY)
    @patch(
        "openai.chat.completions.create",
        return_value=get_mock_completion_response(),
    )
    @patch(
        "sys.argv",
        [from_prompt.__file__, "-c", "Jane Fernbrook", "--api-key", API_KEY, PROMPT],
    )
    def test_from_prompt_stderr(self, completions_create: Mock) -> None:
        """
        Should print any runtime errors from the generated SQL to stderr
        """
        self.mock_execute_sql_query.side_effect = Exception("SQL Error")

        out = StringIO()
        err = StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            from_prompt.main()
            self.assertIn("Error executing query: SQL Error", err.getvalue())
