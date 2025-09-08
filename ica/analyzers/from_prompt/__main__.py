#!/usr/bin/env python3

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

import openai
from openai.types.chat import ChatCompletion

import ica

MODEL: Final[str] = "gpt-4.1"
ICA_REPO: Final[str] = os.getcwd()
README_PATH: Final[str] = os.path.join(ICA_REPO, "README.md")
ANALYZERS_DIR: Final[str] = os.path.join(ICA_REPO, "ica/analyzers")
PROMPT_TEMPLATE_PATH: Final[str] = os.path.join(
    os.path.dirname(__file__),
    "system-prompt.txt",
)


def get_analyzer_files() -> list[str]:
    """Retrieve the paths of all analyzer files to send to the model"""
    return [
        os.path.join(ANALYZERS_DIR, fname)
        for fname in os.listdir(ANALYZERS_DIR)
        if fname.endswith(".py") and fname != "__init__.py"
    ]


def build_system_prompt() -> str:
    """
    Construct the system prompt to send to the model by reading in the README
    and all existing analyzer code files
    """
    readme = Path(README_PATH).read_text()
    analyzers_content = "\n\n".join(
        f"# {Path(f).name}\n" + Path(f).read_text() for f in get_analyzer_files()
    )
    template = Path(PROMPT_TEMPLATE_PATH).read_text()
    return template.format(readme=readme, analyzers_content=analyzers_content)


def generate_analyzer_code(prompt: str, system_prompt: str) -> ChatCompletion:
    """Send the prompts to the OpenAI API and return the response"""
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
    """Extract the analyzer code from a GFM fenced code block in the response"""
    # content can be None depending on SDK types; guard to satisfy type checker
    content = response.choices[0].message.content
    code = (content or "").strip()
    match = re.search(r"(`{3,4})(python)?\n(.*?)\n\1", code, re.DOTALL)
    if match:
        code = match.group(3).strip()
    return code


def main() -> None:
    """
    Use the OpenAI API to generate an ICA analyzer from the supplied prompt,
    then execute the generated code
    """
    cli_parser = ica.get_cli_parser()
    cli_parser.add_argument(
        "--api-key",
        "-k",
        help="API key to send to the OpenAI API",
    )
    cli_parser.add_argument(
        "--write",
        "-w",
        help="Writes the generated analyzer to disk before executing it",
    )
    cli_parser.add_argument(
        "prompt",
        help="Prompt describing the analyzer to generate",
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
    if cli_args.write:
        # Optionally write the generated code to a file before executing it
        analyzer_file_path = Path(cli_args.write).expanduser().resolve()
        print(f"Writing analyzer to {cli_args.write}")
        analyzer_file_path.write_text(code)
        cmd = [sys.executable, str(analyzer_file_path)] + sys.argv[1:]
    else:
        cmd = [sys.executable, "-"] + sys.argv[1:]
    print("Running analyzer...")
    result = subprocess.run(
        cmd,
        input=f"{code}\n",
        text=True,
        # Roll the printing of stdout/stderr back up to the parent process so
        # that stdout can be captured by our tests
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)


if __name__ == "__main__":
    main()
