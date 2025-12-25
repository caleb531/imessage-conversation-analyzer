#!/usr/bin/env python3

import ica


def main() -> None:
    """
    Execute a SQL query against the database of all ICA dataframes
    """
    parser = ica.get_cli_parser()
    parser.add_argument("query", help="the SQL query to execute")
    cli_args = parser.parse_args()

    dfs = ica.get_dataframes(
        contact=cli_args.contact,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    # Execute the query and print the resulting dataframe to stdout
    with ica.get_sql_connection(dfs) as con:
        result_df = ica.execute_sql_query(cli_args.query, con)
        ica.output_results(
            result_df,
            format=cli_args.format,
            output=cli_args.output,
        )


if __name__ == "__main__":
    main()
