#!/usr/bin/env python3

import re

import ica


def main() -> None:

    cli_args = ica.get_cli_args()
    phrase = cli_args.args[0]
    if not phrase:
        raise Exception("Phrase to count must be provided")
    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name, timezone=cli_args.timezone
    )
    filtered_messages = dfs.messages[~dfs.messages["is_reaction"]]
    count = (
        filtered_messages["text"]
        .str.findall(phrase, flags=re.IGNORECASE)
        .str.len()
        .sum()
    )
    print(f"The phrase '{phrase}' appears {count} times.")


if __name__ == "__main__":
    main()
