#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path
from typing import Final

import openai
from openai.types.chat import ChatCompletion

import ica  # type: ignore

MODEL: Final[str] = "gpt-4.1"
ICA_REPO: Final[str] = os.path.join(
    os.path.expanduser("~"),
    "Repositories",
    "personal",
    "imessage-conversation-analyzer",
)
README_PATH: Final[str] = os.path.join(ICA_REPO, "README.md")
ANALYZERS_DIR: Final[str] = os.path.join(ICA_REPO, "ica/analyzers")
PROMPT_TEMPLATE_PATH: Final[str] = os.path.join(
    os.path.dirname(__file__),
    "system-prompt.txt",
)


def get_analyzer_files() -> list[str]:
    return [
        os.path.join(ANALYZERS_DIR, fname)
        for fname in os.listdir(ANALYZERS_DIR)
        if fname.endswith(".py") and fname != "__init__.py"
    ]


def build_system_prompt() -> str:
    readme = Path(README_PATH).read_text()
    analyzers_content = "\n\n".join(
        f"# {Path(f).name}\n" + Path(f).read_text() for f in get_analyzer_files()
    )
    template = Path(PROMPT_TEMPLATE_PATH).read_text()
    return template.format(readme=readme, analyzers_content=analyzers_content)


def get_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found in .env file.", file=sys.stderr)
        sys.exit(1)
    return api_key


def generate_analyzer_code(prompt: str, system_prompt: str) -> ChatCompletion:
    print(f"Generating analyzer with AI ({MODEL})...")
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
    )
    return response


def parse_code_from_response(response: ChatCompletion) -> str:
    # content can be None depending on SDK types; guard to satisfy type checker
    content = response.choices[0].message.content
    code = (content or "").strip()
    if code.startswith("````python"):
        code = code.split("````python", 1)[-1].split("````", 1)[0].strip()
    elif code.startswith("```python"):
        code = code.split("```python", 1)[-1].split("```", 1)[0].strip()
    elif code.startswith("```"):
        code = code.split("```", 1)[-1].split("```", 1)[0].strip()
    return code


def get_analyzer_file_path(code: str) -> str:
    # Extract analyzer name from the first line
    return os.path.relpath(
        os.path.join(
            os.path.dirname(__file__), code.splitlines()[1][1:].strip() if code else ""
        ),
        ".",
    )


def main() -> None:
    cli_parser = ica.get_cli_parser()
    cli_parser.add_argument(
        "--api-key",
        "-k",
        help="API key to send to the OpenAI API.",
    )
    cli_parser.add_argument(
        "prompt",
        help="Prompt describing the analyzer to generate.",
    )
    cli_args = cli_parser.parse_args()

    openai.api_key = cli_args.api_key
    system_prompt = build_system_prompt()
    response: ChatCompletion = generate_analyzer_code(cli_args.prompt, system_prompt)
    # Print token usage
    usage = getattr(response, "usage", None)
    if usage:
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        print(f"Input Tokens: {prompt_tokens:,}")
        print(f"Output Tokens: {completion_tokens:,}")
    else:
        print("Token usage information not available.")
    code = parse_code_from_response(response)
    # Execute the generated analyzer code by piping it to Python via stdin
    cmd = [sys.executable, "-"] + sys.argv[1:]
    print("Running analyzer...")
    subprocess.run(cmd, input=f"{code}\n", text=True)


if __name__ == "__main__":
    main()
