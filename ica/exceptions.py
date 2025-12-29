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


class ContactWithSameNameError(BaseAnalyzerException):
    """
    Raised when multiple contacts with the same name are found
    """

    pass


class ConversationNotFoundError(BaseAnalyzerException):
    """
    Raised when no conversation was found for the specified contact
    """

    pass


class DateRangeInvalidError(BaseAnalyzerException):
    """
    Raised when the specified date range is mismatched (e.g. the start date is
    after the end date)
    """

    pass


class FormatNotSupportedError(BaseAnalyzerException):
    """
    Raised when the specified format is not supported by the library
    """

    pass
