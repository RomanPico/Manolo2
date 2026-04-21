"""LLM client errors."""


class LLMClientError(Exception):
    """Base error for LLM operations."""


class LLMHTTPError(LLMClientError):
    """HTTP layer failure."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LLMResponseError(LLMClientError):
    """Unexpected response shape."""
