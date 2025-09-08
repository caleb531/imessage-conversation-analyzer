class EmptyResponseError(Exception):
    """Raised when the OpenAI API returns an empty response"""

    pass


class ResponseMissingCodeError(Exception):
    """Raised when the OpenAI API response does not contain any code"""

    pass
