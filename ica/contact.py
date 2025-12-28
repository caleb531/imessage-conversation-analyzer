#!/usr/bin/env python3
import glob
import importlib.resources
import os
import sqlite3
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass, field
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


@dataclass
class ContactRecord:
    # The first and last name of the contact
    first_name: str
    last_name: str
    # The phone numbers and email addresses associated with the contact
    phone_numbers: list[str] = field(default_factory=list)
    email_addresses: list[str] = field(default_factory=list)

    def get_identifiers(self) -> list[str]:
        """
        Retrieve the identifiers for the contact that may be stored on the
        messages database
        """
        return sorted(set(self.phone_numbers + self.email_addresses))


def get_contact_record(
    con: sqlite3.Connection, contact_identifier: str
) -> ContactRecord:
    contact_identifier = normalize_contact_identifier(contact_identifier)

    rows = pd.read_sql_query(
        sql=importlib.resources.files("ica")
        .joinpath(os.path.join("queries", "contact.sql"))
        .read_text(),
        con=con,
        params={"contact_identifier": contact_identifier},
    )

    if rows.empty:
        raise ContactNotFoundError(f"Contact '{contact_identifier}' not found")

    first_name = (
        rows["ZFIRSTNAME"].dropna().iloc[0]
        if not rows["ZFIRSTNAME"].dropna().empty
        else ""
    )
    last_name = (
        rows["ZLASTNAME"].dropna().iloc[0]
        if not rows["ZLASTNAME"].dropna().empty
        else ""
    )

    phone_numbers = (
        rows["ZFULLNUMBER"].apply(normalize_phone_number).dropna().unique().tolist()
    )
    email_addresses = (
        rows["ZADDRESS"].apply(normalize_email_address).dropna().unique().tolist()
    )

    return ContactRecord(
        first_name=first_name,
        last_name=last_name,
        phone_numbers=phone_numbers,
        email_addresses=email_addresses,
    )


def get_contact_records(contact_identifiers: Sequence[str]) -> list[ContactRecord]:
    """
    Fetch the attributes for the given contact identifiers; each user-supplied
    identifier could be a full name, phone number, or email address; all
    identifiers may not represent the same contact
    """
    records: list[ContactRecord] = []
    # There is a separate AddressBook database file for each "source" of
    # contacts (e.g. On My Mac, iCloud, etc.); we must query each of these
    # databases and combine the separate results into a single result set
    for db_path in glob.iglob(str(DB_GLOB)):
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as con:
            records.extend(
                (
                    get_contact_record(con, contact_identifier)
                    for contact_identifier in contact_identifiers
                )
            )

    return records
