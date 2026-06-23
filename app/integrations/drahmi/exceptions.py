"""Drahmi integration errors."""

from __future__ import annotations


class DrahmiError(Exception):
    """Invalid configuration or request parameters for Drahmi."""


class DrahmiApiError(DrahmiError):
    """Drahmi HTTP API returned an error."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
