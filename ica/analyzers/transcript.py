#!/usr/bin/env python3

import ica


def main() -> None:
    """
    Generates a full, unedited transcript of every message, including
    reactions, between you and the other person (attachment files not included)
    """
    cli_args = ica.get_cli_parser().parse_args(namespace=ica.TypedCLIArguments())
    data = ica.get_conversation_data(
        contact_name=cli_args.contact_name,
        timezone=cli_args.timezone,
        from_date=cli_args.from_date,
        to_date=cli_args.to_date,
        from_person=cli_args.from_person,
    )

    rel = data.messages.project(
        """
        datetime as timestamp,
        CASE WHEN is_from_me THEN 'Yes' ELSE 'No' END as is_from_me,
        CASE WHEN is_reaction IS NOT NULL THEN 'Yes' ELSE 'No' END as is_reaction,
        regexp_replace(text, '\ufffc', '(attachment)', 'g') as message
        """
    ).order("timestamp")

    ica.output_results(
        rel,
        format=cli_args.format,
        output=cli_args.output,
    )


if __name__ == "__main__":
    main()
