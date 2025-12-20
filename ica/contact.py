#!/usr/bin/env python3

import glob
import importlib.resources
import os
import sqlite3
from pathlib import Path
from typing import Optional

import phonenumbers
import polars as pl

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


def get_chat_identifiers(contact_name: str) -> list[str]:
    """
    Fetch the sequence of chat identifiers for the contact with the given name
    """
    chat_identifiers: set[str] = set()
    # There is a separate AddressBook database file for each "source" of
    # contacts (e.g. On My Mac, iCloud, etc.); we must query each of these
    # databases and combine the separate results into a single result set
    for db_path in glob.iglob(str(DB_GLOB)):
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as con:
            cursor = con.cursor()
            query = (
                importlib.resources.files("ica")
                .joinpath(os.path.join("queries", "contact.sql"))
                .read_text()
            )
            cursor.execute(query, {"contact_name": contact_name})
            rows = pl.DataFrame(
                cursor.fetchall(), schema=["ZFULLNUMBER", "ZADDRESS"], orient="row"
            )

            # Combine the results
            chat_identifiers.update(
                rows["ZFULLNUMBER"]
                .map_elements(normalize_phone_number, return_dtype=pl.Utf8)
                # The normalization function will convert empty strings to None
                # so that we can filter them out with drop_nulls()
                .drop_nulls()
            )
            chat_identifiers.update(
                rows["ZADDRESS"]
                .map_elements(normalize_email_address, return_dtype=pl.Utf8)
                # The normalization function will convert empty strings to None
                # so that we can filter them out with drop_nulls()
                .drop_nulls()
            )

    # Quit if the contact with the specified name could not be found
    if not len(chat_identifiers):
        raise ContactNotFoundError(f'No contact found with the name "{contact_name}"')

    return sorted(chat_identifiers)
