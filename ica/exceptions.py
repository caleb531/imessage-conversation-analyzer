#!/usr/bin/env python3


class BaseAnalyzerException(Exception):
    """A base exception class for iMessage Conversation Analyzer"""

    pass


class ContactNotFoundError(BaseAnalyzerException):
    """
    Raised when the specified contact was not found in the Contacts database
    """

    pass


class ConversationNotFoundError(BaseAnalyzerException):
    """
    Raised when no conversation was found for the specified contact
    """

    pass


class OutputRequiredError(BaseAnalyzerException):
    """
    Raised when the specified format is xlsx/excel but no output path is
    provided
    """

    pass
