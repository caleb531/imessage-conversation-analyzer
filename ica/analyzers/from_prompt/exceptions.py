class EmptyResponseError(Exception):
    """Raised when the OpenAI API returns an empty response"""

    pass


class ResponseMissingSQLError(Exception):
    """Raised when the OpenAI API response does not contain any SQL"""

    pass
