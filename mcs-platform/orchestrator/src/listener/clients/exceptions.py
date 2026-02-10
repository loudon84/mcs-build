"""Exceptions for API clients."""


class AlimailClientError(Exception):
    """Base exception for Alimail client errors."""

    pass


class AlimailAuthError(AlimailClientError):
    """Authentication error (invalid credentials, token expired, etc.)."""

    pass


class AlimailAPIError(AlimailClientError):
    """API error (4xx, 5xx responses)."""

    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        """Initialize API error."""
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
