#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path
from typing import Final, Union

import openai
from openai.types.chat import ChatCompletion

import ica
from ica.analyzers.from_prompt.exceptions import (
    EmptyResponseError,
    ResponseMissingSQLError,
)

MODEL: Final[str] = "gpt-4.1"
PROMPT_TEMPLATE_PATH: Final[str] = os.path.join(
    os.path.dirname(__file__),
    "system-prompt.txt",
)


def build_system_prompt() -> str:
    """
    Construct the system prompt to send to the model
    """
    return Path(PROMPT_TEMPLATE_PATH).read_text()


def generate_sql(prompt: str, system_prompt: str) -> ChatCompletion:
    """Send the prompts to the OpenAI API and return the response"""
    print(f"Generating SQL with AI ({MODEL})...")
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
    )
    return response


def parse_sql_from_response(response: ChatCompletion) -> str:
    """Extract the SQL query from a GFM fenced code block in the response"""
    # content can be None depending on SDK types; guard to satisfy type checker
    content = response.choices[0].message.content
    if not content:
        raise EmptyResponseError("No content in response from OpenAI API")
    match = re.search(
        r"(`{3,4})(sql)?\n(.*?)\n\1",
        content.strip(),
        re.DOTALL,
    )
    if not match:
        raise ResponseMissingSQLError("No SQL in response from OpenAI API")
    return match.group(3).strip()


class FromPromptCLIArguments(ica.TypedCLIArguments):
    api_key: str
    write: Union[str, None]
    prompt: str


def main() -> None:
    """
    Use the OpenAI API to generate a SQL query from the supplied prompt,
    then execute the generated query
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
        help="Writes the generated SQL to disk before executing it",
    )
    cli_parser.add_argument(
        "prompt",
        help="Prompt describing the data to retrieve",
    )
    cli_args = cli_parser.parse_args(namespace=FromPromptCLIArguments())

    openai.api_key = cli_args.api_key
    system_prompt = build_system_prompt()
    response: ChatCompletion = generate_sql(cli_args.prompt, system_prompt)

    # Print token usage
    usage = getattr(response, "usage", None)
    if usage:
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        print(f"Input Tokens: {prompt_tokens:,}")
        print(f"Output Tokens: {completion_tokens:,}")
    else:
        print("Token usage information not available.")

    query = parse_sql_from_response(response)

    if cli_args.write:
        # Optionally write the generated SQL to a file
        sql_file_path = Path(cli_args.write).expanduser().resolve()
        print(f"Writing SQL to {cli_args.write}")
        sql_file_path.write_text(query)

    print("Running query...")

    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    # Execute the query and output the resulting dataframe
    with ica.get_sql_connection(dfs) as con:
        try:
            result_df = ica.execute_sql_query(query, con=con)
            ica.output_results(
                result_df, format=cli_args.format, output=cli_args.output
            )
        except Exception as error:
            print(f"Error executing query: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
