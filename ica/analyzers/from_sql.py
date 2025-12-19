#!/usr/bin/env python3

import sys

import ica


def main() -> None:
    """
    Execute a SQL query against the database of all ICA dataframes
    """
    parser = ica.get_cli_parser()
    parser.add_argument("query", help="the SQL query to execute")
    cli_args = parser.parse_args()

    data = ica.get_conversation_data(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    # Execute the query and print the resulting dataframe to stdout
    con = ica.get_sql_connection(data)

    # Register views for messages and attachments so user can query them
    data.messages.create_view("messages", replace=True)
    data.attachments.create_view("attachments", replace=True)

    try:
        result_rel = ica.execute_sql_query(cli_args.query, con)
        ica.output_results(
            result_rel,
            format=cli_args.format,
            output=cli_args.output,
        )
    except Exception as error:
        print(f"Error executing query: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
