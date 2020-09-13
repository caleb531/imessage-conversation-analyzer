#!/usr/bin/env python3

import os
import os.path
import sqlite3
import sys

import pandas


def get_db_path():

    return os.path.expanduser(os.path.join(
        '~', 'Library', 'Messages', 'chat.db'))


# Return the parameterized SQL query that retrieves an entire iMessage
# conversation thread
def get_sql_query(query_name):

    with open(f'ica/queries/{query_name}.sql', 'r') as query_file:
        query = query_file.read()

    return query


# Return a pandas dataframe representing all messages in a particular conversation
def get_messages_dataframe(phone_number):

    with sqlite3.connect(get_db_path()) as connection:
        return pandas.read_sql_query(
            sql=get_sql_query('messages'),
            con=connection,
            params={
                'phone_number': phone_number
            })


def run(phone_number):

    messages_dataframe = get_messages_dataframe(phone_number)
    total_message_count = len(messages_dataframe.index)
    if not total_message_count:
        print('Conversation not found', file=sys.stderr)
        sys.exit(1)
    print(f'{total_message_count:,} total messages!')
    # for index, row in messages_dataframe.iterrows():
    #     print(row)
    #     print('')
