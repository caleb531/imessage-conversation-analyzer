#!/usr/bin/env python3


class BaseAnalyzerException(Exception):
    """
    A base exception class for iMessage Conversation Analyzer
    """

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


class FormatNotSupportedError(BaseAnalyzerException):
    """
    Raised when the specified format is not supported by the library
    """

    pass
