#!/usr/bin/env python3

import sqlite3
import sys

import pandas as pd

import ica


def main() -> None:
    """
    Execute a SQL query against the database of all ICA dataframes
    """
    parser = ica.get_cli_parser()
    parser.add_argument("query", help="the SQL query to execute")
    cli_args = parser.parse_args()

    dfs = ica.get_dataframes(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    # Create an in-memory SQLite database and load the dataframes into it
    with sqlite3.connect(":memory:") as conn:
        # Write dataframes to SQLite; we convert datetime columns to strings or
        # let to_sql handle them (it usually handles them well), but for
        # consistency with how one might query, ensuring they are accessible is
        # key. The pandas to_sql() method handles datetimes by converting to
        # timestamp strings usually.

        dfs.messages.to_sql("messages", conn, index=False)
        dfs.attachments.to_sql("attachments", conn, index=False)

        # Execute the query and output the resulting dataframe
        try:
            result_df = pd.read_sql_query(cli_args.query, conn)
            ica.output_results(
                result_df,
                format=cli_args.format,
                output=cli_args.output,
            )
        except Exception as e:
            print(f"Error executing query: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
