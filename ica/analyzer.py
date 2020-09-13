#!/usr/bin/env python3

import os
import os.path
import sqlite3
import sys
import types

import pandas


# Retrieve the path to the database file for the macOS Messages application
def get_db_path():

    return os.path.expanduser(os.path.join(
        '~', 'Library', 'Messages', 'chat.db'))


# Return the parameterized SQL query that retrieves an entire iMessage
# conversation thread
def get_sql_query(query_name):

    with open(f'ica/queries/{query_name}.sql', 'r') as query_file:
        query = query_file.read()

    return query


# Return a pandas dataframe representing all messages in a particular
# conversation (identified by the given phone number)
def get_messages_dataframe(connection, phone_number):

    return pandas.read_sql_query(
        sql=get_sql_query('messages'),
        con=connection,
        params={'phone_number': phone_number},
        parse_dates={
            'date': {'infer_datetime_format': True}
        })


# Return a pandas dataframe representing all attachments in a particular
# conversation (identified by the given phone number)
def get_attachments_dataframe(connection, phone_number):

    return pandas.read_sql_query(
        sql=get_sql_query('attachments'),
        con=connection,
        params={'phone_number': phone_number})


# Return all dataframes for a specific macOS Messages conversation
def get_dataframes(phone_number):

    with sqlite3.connect(get_db_path()) as connection:
        return types.SimpleNamespace(
            messages=get_messages_dataframe(connection, phone_number),
            attachments=get_attachments_dataframe(connection, phone_number))


# Analyze the macOS Messages conversation with the given recipient phone number
def run(phone_number):

    dataframes = get_dataframes(phone_number)

    total_message_count = len(dataframes.messages.index)
    if not total_message_count:
        print('Conversation not found', file=sys.stderr)
        sys.exit(1)

    total_gif_count = dataframes.attachments.mime_type.eq('image/gif').sum()

    print(f'{total_message_count:,} total messages!')
    print(f'{total_gif_count:,} total GIFs!')
    # for index, row in dataframes.messages.iterrows():
    #     print(row)
    #     print('')
