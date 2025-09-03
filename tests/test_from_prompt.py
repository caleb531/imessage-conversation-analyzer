import types
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import ica.analyzers.from_prompt.__main__ as from_prompt
from tests.utils import ICATestCase, temp_ica_dir, use_env

API_KEY = "abc"
PROMPT = "test prompt"

MOCK_ANALYZER_CONTENTS = Path(
    "tests/data/analyzers/generated_from_prompt.py"
).read_text()


def get_mock_completion_response(
    content: str = f"```python\n{MOCK_ANALYZER_CONTENTS}\n```",
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
        Should call the OpenAI API to generate an analyzer, then run that
        analyzer code, printing usage information when available
        """
        out = StringIO()
        with redirect_stdout(out):
            from_prompt.main()
            _, kwargs = completions_create.call_args
            self.assertEqual(kwargs["model"], from_prompt.MODEL)
            self.assertEqual(kwargs["max_tokens"], 4096)
            self.assertEqual(kwargs["messages"][0]["role"], "system")
            self.assertEqual(kwargs["messages"][1]["role"], "user")
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
        Should call the OpenAI API to generate an analyzer, then run that
        analyzer code, informing the user when usage information is unavailable
        """
        out = StringIO()
        with redirect_stdout(out):
            from_prompt.main()
            _, kwargs = completions_create.call_args
            self.assertEqual(kwargs["model"], from_prompt.MODEL)
            self.assertEqual(kwargs["max_tokens"], 4096)
            self.assertEqual(kwargs["messages"][0]["role"], "system")
            self.assertEqual(kwargs["messages"][1]["role"], "user")
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
    def test_from_prompt_keep_analyzer(self, completions_create: Mock) -> None:
        """
        Should write the generated analyzer to disk when the option is passed
        """
        out = StringIO()
        generated_analyzer_file_name = "generated_from_prompt.py"
        generated_analyzer_file_path = f"{temp_ica_dir}/{generated_analyzer_file_name}"
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
                    generated_analyzer_file_path,
                    PROMPT,
                ],
            ),
        ):
            from_prompt.main()
            self.assertEqual(
                Path(generated_analyzer_file_path).read_text().rstrip(),
                Path(f"tests/data/analyzers/{generated_analyzer_file_name}")
                .read_text()
                .rstrip(),
            )
