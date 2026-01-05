#!/usr/bin/env python3
import glob
import importlib.resources
import os
import sqlite3
from collections import Counter
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd
import phonenumbers

from ica.exceptions import ContactNotFoundError, ContactWithSameNameError

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
    # The unique identifier for the contact in the AddressBook database
    id: str
    # The first and last name of the contact
    first_name: str
    last_name: str
    # The phone numbers and email addresses associated with the contact
    phone_numbers: list[str] = field(default_factory=list)
    email_addresses: list[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_identifiers(self) -> set[str]:
        """
        Retrieve the identifiers for the contact that may be stored on the
        messages database
        """
        return set(self.phone_numbers + self.email_addresses)


def get_contact_record(
    con: sqlite3.Connection, contact_identifier: str
) -> list[ContactRecord]:
    contact_identifier = normalize_contact_identifier(contact_identifier)

    rows = pd.read_sql_query(
        sql=importlib.resources.files("ica")
        .joinpath(os.path.join("queries", "contact.sql"))
        .read_text(),
        con=con,
        params={"contact_identifier": contact_identifier},
    )

    records = []
    if rows.empty:
        return records

    for contact_id, group in rows.groupby("contact_id"):
        first_name = group["ZFIRSTNAME"].iloc[0] or ""
        last_name = group["ZLASTNAME"].iloc[0] or ""

        phone_numbers = (
            group["ZFULLNUMBER"]
            .apply(normalize_phone_number)
            .dropna()
            .unique()
            .tolist()
        )
        email_addresses = (
            group["ZADDRESS"].apply(normalize_email_address).dropna().unique().tolist()
        )

        records.append(
            ContactRecord(
                first_name=first_name,
                last_name=last_name,
                phone_numbers=phone_numbers,
                email_addresses=email_addresses,
                id=str(contact_id),
            )
        )

    return records


def coalesce_contact_records(records: list[ContactRecord]) -> list[ContactRecord]:
    """
    Merge contact records that share at least one identifier (phone number or
    email address)
    """
    # A list of merged contact records
    unique_records: list[ContactRecord] = []
    for record in records:
        found = False
        for unique_record in unique_records:
            # If any identifier overlaps, merge
            if record.get_identifiers() & unique_record.get_identifiers():
                # Merge identifiers
                unique_record.phone_numbers = sorted(
                    set(unique_record.phone_numbers) | set(record.phone_numbers)
                )
                unique_record.email_addresses = sorted(
                    set(unique_record.email_addresses) | set(record.email_addresses)
                )
                # Optionally, update names if needed (e.g., keep the longest, or
                # prefer non-empty)
                if not unique_record.first_name and record.first_name:
                    unique_record.first_name = record.first_name
                if not unique_record.last_name and record.last_name:
                    unique_record.last_name = record.last_name
                unique_record.id = record.id
                found = True
                break
        # If no overlapping record was found, add as new
        if not found:
            unique_records.append(record)
    return unique_records


def get_unique_contact_display_name(
    contact_records: Sequence[ContactRecord], contact_record: ContactRecord
) -> str:
    """
    Determine the unique display name for the given contact record, falling back
    to more specific identifiers if necessary to avoid ambiguity
    """
    # 1. First name
    first_name_count = sum(
        1 for c in contact_records if c.first_name == contact_record.first_name
    )
    if first_name_count == 1:
        return contact_record.first_name

    # 2. Full name
    full_name_count = sum(
        1 for c in contact_records if c.full_name == contact_record.full_name
    )
    if full_name_count == 1:
        return contact_record.full_name

    # 3. Phone number
    if contact_record.phone_numbers:
        phone_number = contact_record.phone_numbers[0]
        phone_number_count = sum(
            1
            for c in contact_records
            if c.phone_numbers and c.phone_numbers[0] == phone_number
        )
        if phone_number_count == 1:
            return phone_number

    # 4. Email address
    if contact_record.email_addresses:
        email_address = contact_record.email_addresses[0]
        email_address_count = sum(
            1
            for c in contact_records
            if c.email_addresses and c.email_addresses[0] == email_address
        )
        if email_address_count == 1:
            return email_address

    return contact_record.full_name or contact_record.first_name or "Unknown"


def validate_contact_records(
    contact_records: list[ContactRecord], contact_identifiers: Sequence[str]
) -> None:
    """
    Validate that at least one contact record was found; if multiple records
    have the same full name, raise an error.
    """
    if not contact_records:
        raise ContactNotFoundError(
            "No contact found for {}".format(", ".join(contact_identifiers))
        )

    # Check for duplicate full names
    # Check for duplicate contacts with the same name but different identifiers
    name_counts = Counter(
        (record.first_name, record.last_name) for record in contact_records
    )
    duplicates = [name for name, count in name_counts.items() if count > 1]
    if duplicates:
        # Only report the first duplicate found
        name = duplicates[0]
        raise ContactWithSameNameError(
            f'Multiple contacts found for name "{name[0]} {name[1]}". Please specify a phone number or email address instead.'  # noqa: E501
        )


def get_contact_records(
    contact_identifiers: Sequence[str],
) -> list[ContactRecord]:
    """
    Fetch the attributes for the given contact identifiers; each user-supplied
    identifier could be a full name, phone number, or email address; all
    identifiers may not represent the same contact. Returns a flat list of
    unique ContactRecord objects.
    """
    all_records: list[ContactRecord] = []
    for db_path in glob.iglob(str(DB_GLOB)):
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as con:
            for contact_identifier in contact_identifiers:
                all_records.extend(get_contact_record(con, contact_identifier))

    # Coalesce all records across all identifiers and sources
    unique_records = coalesce_contact_records(all_records)
    validate_contact_records(unique_records, contact_identifiers)
    return unique_records
