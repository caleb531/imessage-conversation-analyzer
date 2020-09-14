#!/usr/bin/env python3

import os
import os.path
import sqlite3
import sys
import types

import pandas as pd


# The respective emojis to count across the entire iMessage conversation
EMOJIS = ('❤️', '😍', '😘', '😂', '😅', '🌙')


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

    return pd.read_sql_query(
        sql=get_sql_query('messages'),
        con=connection,
        params={'phone_number': phone_number},
        parse_dates={
            'datetime': {'infer_datetime_format': True}
        })


# Return a pandas dataframe representing all attachments in a particular
# conversation (identified by the given phone number)
def get_attachments_dataframe(connection, phone_number):

    return pd.read_sql_query(
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
def analyze_conversation(phone_number):

    dataframes = get_dataframes(phone_number)

    pd.options.display.float_format = '{:,}'.format

    # Total number of messages since the conversation was created
    total_message_count = len(dataframes.messages.index)
    if not total_message_count:
        print('Conversation not found', file=sys.stderr)
        sys.exit(1)
    print(f'{total_message_count:,} total messages!')

    # Total number of GIFs across all messages
    total_gif_count = dataframes.attachments.mime_type.eq('image/gif').sum()
    print(f'{total_gif_count:,} total GIFs!')

    # Output the occurrences of specific emojis
    most_frequent_emojis = pd.DataFrame({
        'emoji': EMOJIS,
        'count': [dataframes.messages.text.str.extract('(' + emoji + ')')
                  .count().item() for emoji in EMOJIS]
    }, columns=['emoji', 'count'])
    print(most_frequent_emojis.sort_values(by='count', ascending=False))

    # Copy the messages dataframe so that we can count all "text" column values
    # by converting them to integers (always 1)
    messages_aggregate = dataframes.messages.copy()
    messages_aggregate['text'] = messages_aggregate.text.apply(
        pd.to_numeric, errors='coerce').isna()
    groups_by_day = messages_aggregate.resample('D', on='datetime')
    sums_by_day = groups_by_day.sum()
    sums_by_day['is_not_from_me'] = (sums_by_day['text']
                                     - sums_by_day['is_from_me'])
    print(sums_by_day)
