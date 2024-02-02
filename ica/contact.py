#!/usr/bin/env python3

import glob
import importlib.resources
import os
import os.path
import sqlite3
from typing import Union

import pandas as pd
import phonenumbers

from ica.exceptions import ContactNotFoundError

# The glob pattern matching all AddressBook SQL databases to read from
DB_GLOB = os.path.expanduser(
    os.path.join(
        "~", "Library", "Application Support", "AddressBook", "Sources", "*", "*.abcddb"
    )
)


# The default region for all phone numbers
DEFAULT_PHONE_NUMBER_REGION = "US"


def normalize_phone_number(phone_number: str) -> Union[str, None]:
    """
    Normalize the given phone number to the format required for searching in the
    iMessage database
    """
    if not phone_number:
        return None
    return phonenumbers.format_number(
        phonenumbers.parse(phone_number, region=DEFAULT_PHONE_NUMBER_REGION),
        phonenumbers.PhoneNumberFormat.E164,
    )


def normalize_email_address(email_address: str) -> Union[str, None]:
    """
    Normalize the given email address to the format required for searching in
    the iMessage database
    """
    if not email_address:
        return None
    normalized_email_address = email_address.strip()
    return normalized_email_address


def get_chat_identifiers(contact_name: str) -> list[str]:
    """
    Fetch the sequence of chat identifiers for the contact with the given name
    """
    chat_identifiers: set[str] = set()
    # There is a separate AddressBook database file for each "source" of
    # contacts (e.g. On My Mac, iCloud, etc.); we must query each of these
    # databases and combine the separate results into a single result set
    for db_path in glob.iglob(DB_GLOB):
        with sqlite3.connect(db_path) as connection:
            rows = pd.read_sql_query(
                sql=importlib.resources.files(__package__)
                .joinpath(os.path.join("queries", "contact.sql"))
                .read_text(),
                con=connection,
                params={"contact_name": contact_name},
            )
            # Combine the results
            chat_identifiers.update(
                rows["ZFULLNUMBER"].apply(normalize_phone_number)
                # The normalization function will convert empty strings to None
                # so that we can filter them out with dropna()
                .dropna()
            )
            chat_identifiers.update(
                rows["ZADDRESS"].apply(normalize_email_address)
                # The normalization function will convert empty strings to None
                # so that we can filter them out with dropna()
                .dropna()
            )

    # Quit if the contact with the specified name could not be found
    if not len(chat_identifiers):
        raise ContactNotFoundError(f'No contact found with the name "{contact_name}"')

    return sorted(chat_identifiers)
