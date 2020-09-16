#!/usr/bin/env python3

import importlib.machinery
import importlib.util
import os
import os.path
import sqlite3
import sys
import types

import pandas as pd
from tabulate import tabulate


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
def analyze_conversation(phone_number, metric_file, format):

    dfs = get_dataframes(phone_number)

    # Quit if no messages were found for the specified conversation
    if not len(dfs.messages.index):
        print('Conversation not found', file=sys.stderr)
        sys.exit(1)

    # Load and execute the given Python file as a module to retrieve the
    # relevant DataFrame
    loader = importlib.machinery.SourceFileLoader('metric_file', metric_file)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    metric_df = module.analyze(dfs)

    # Make all indices start from 1 instead of 0, but only if the index is the
    # default (rather than a custom column)
    is_default_index = (not metric_df.index.name)
    if is_default_index:
        metric_df.index += 1

    # Output executed DataFrame to correct format
    if format == 'csv':
        print(metric_df.to_csv(index=not is_default_index))
    else:
        print(tabulate(metric_df,
                       showindex=not is_default_index,
                       headers=metric_df.columns))
