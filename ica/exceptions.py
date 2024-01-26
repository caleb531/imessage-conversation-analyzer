#!/usr/bin/env python3


class BaseAnalyzerException(Exception):
    """A base exception class for iMessage Conversation Analyzer"""

    pass


class InvalidPhoneNumberError(BaseAnalyzerException):
    """
    Raised when the phone number provided to an analyzer is in an invalid format
    """

    pass


class ContactNotFoundError(BaseAnalyzerException):
    """
    Raised when the specified contact was not found in the Contacts database
    """

    pass
