#!/usr/bin/env python3


class BaseAnalyzerException(Exception):
    """A base exception class for iMessage Conversation Analyzer"""

    pass


class ContactNotFoundError(BaseAnalyzerException):
    """
    Raised when the specified contact was not found in the Contacts database
    """

    pass