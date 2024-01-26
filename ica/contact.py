#!/usr/bin/env python3

import glob
import importlib.resources
import os
import os.path
import re
import sqlite3

import pandas as pd

from ica.exceptions import ContactNotFoundError, InvalidPhoneNumberError

# The glob pattern matching all AddressBook SQL databases to read from
DB_GLOB = os.path.expanduser(
    os.path.join(
        "~", "Library", "Application Support", "AddressBook", "Sources", "*", "*.abcddb"
    )
)


# Normalize the given phone number to the format required for searching in the
# iMessage database
def normalize_phone_number(phone_number: str) -> str:
    # Strip all non-digits
    normalized_phone_number = re.sub("[^0-9]", "", phone_number)
    # Phone number must have area code
    if len(normalized_phone_number) < 10:
        raise InvalidPhoneNumberError(f"Phone number {phone_number} missing area code")
    # Add US country code if missing
    if len(normalized_phone_number) == 10:
        normalized_phone_number = "1" + normalized_phone_number
    normalized_phone_number = "+" + normalized_phone_number
    return normalized_phone_number


# Normalize the given email address to the format required for searching in the
# iMessage database
def normalize_email_address(email_address: str) -> str:
    normalized_email_address = email_address.strip()
    return normalized_email_address


# Fetch the sequence of chat identifiers for the contact with the given name
def get_chat_identifiers(contact_name: str) -> list[str]:
    chat_identifiers: set[str] = set()
    # There is a separate AddressBook database file for each "source" of
    # contacts (e.g. On My Mac, iCloud, etc.); we must query each of these
    # databases and combine the separate results into a single result set
    for db_path in glob.iglob(DB_GLOB):
        with sqlite3.connect(db_path) as connection:
            rows = pd.read_sql_query(
                sql=importlib.resources.files(__package__)
                .joinpath("queries/contact.sql")
                .read_text(),
                con=connection,
                params={"contact_name": contact_name},
            )
            # Combine the results
            chat_identifiers.update(
                normalize_phone_number(phone_number)
                for phone_number in rows["ZFULLNUMBER"]
                if phone_number
            )
            chat_identifiers.update(
                normalize_email_address(email_address)
                for email_address in rows["ZADDRESS"]
                if email_address
            )

    # Quit if the contact with the specified name could not be found
    if not len(chat_identifiers):
        raise ContactNotFoundError(f'No contact found with the name "{contact_name}"')

    return sorted(chat_identifiers)
