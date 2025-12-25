#!/usr/bin/env python3
import glob
import importlib.resources
import os
import sqlite3
from contextlib import suppress
from pathlib import Path
from typing import Optional

import pandas as pd
import phonenumbers

from ica.exceptions import ContactNotFoundError

# The glob pattern matching all AddressBook SQL databases to read from
DB_GLOB = (
    Path.home()
    / "Library"
    / "Application Support"
    / "AddressBook"
    / "Sources"
    / "*"
    / "*.abcddb"
)


# The default region for all phone numbers
DEFAULT_PHONE_NUMBER_REGION = "US"


def normalize_phone_number(phone_number: str) -> Optional[str]:
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


def normalize_email_address(email_address: str) -> Optional[str]:
    """
    Normalize the given email address to the format required for searching in
    the iMessage database
    """
    if not email_address:
        return None
    normalized_email_address = email_address.strip()
    return normalized_email_address


def normalize_contact_identifier(contact_identifier: str) -> str:
    """
    Normalize the given contact identifier (i.e. full name, phone number, or
    email address) to the format required for searching in the contacts database
    """
    with suppress(phonenumbers.NumberParseException):
        # If the contact string is a valid phone number, we should strip the
        # country code and use the national number (i.e. the phone number minus
        # the country code) for the search; this allows us to find the contact
        # regardless of whether or not the country code is stored in the
        # database (since the contacts database stores each phone number as the
        # user typed it, the country code may or may not be present)
        parsed_phone = phonenumbers.parse(
            contact_identifier, region=DEFAULT_PHONE_NUMBER_REGION
        )
        if phonenumbers.is_valid_number(parsed_phone):
            return str(parsed_phone.national_number)
    return contact_identifier


def get_chat_identifiers(contact_identifier: str) -> list[str]:
    """
    Fetch the sequence of chat identifiers for the contact with the given
    contact identifier (i.e. full name, phone number, or email address)
    """

    contact_identifier = normalize_contact_identifier(contact_identifier)

    chat_identifiers: set[str] = set()
    # There is a separate AddressBook database file for each "source" of
    # contacts (e.g. On My Mac, iCloud, etc.); we must query each of these
    # databases and combine the separate results into a single result set
    for db_path in glob.iglob(str(DB_GLOB)):
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as con:
            rows = pd.read_sql_query(
                sql=importlib.resources.files("ica")
                .joinpath(os.path.join("queries", "contact.sql"))
                .read_text(),
                con=con,
                params={"contact_identifier": contact_identifier},
            )
            # Combine the results
            chat_identifiers.update(
                rows["ZFULLNUMBER"]
                .apply(normalize_phone_number)
                # The normalization function will convert empty strings to None
                # so that we can filter them out with dropna()
                .dropna()
            )
            chat_identifiers.update(
                rows["ZADDRESS"]
                .apply(normalize_email_address)
                # The normalization function will convert empty strings to None
                # so that we can filter them out with dropna()
                .dropna()
            )

    # Quit if the contact with the specified name could not be found
    if not len(chat_identifiers):
        raise ContactNotFoundError(
            f'No contact found with the name "{contact_identifier}"'
        )

    return sorted(chat_identifiers)
