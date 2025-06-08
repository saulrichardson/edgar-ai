"""Minimal stub of *pydantic-settings* for offline/test environments.

This is *not* a full replacement—only what *edgar_ai* currently relies upon:
    • BaseSettings (inherits from pydantic.BaseModel)
    • SettingsConfigDict (alias of dict)

If the real package is available, the application should use it instead. This
stub exists solely to guarantee tests run in environments without PyPI
connectivity.  It is intentionally private to the *edgar_ai* distribution.
"""

from __future__ import annotations

from pydantic import BaseModel


class SettingsConfigDict(dict):
    """Type alias to mimic the original."""


class BaseSettings(BaseModel):
    """Very small subset mimicking pydantic-settings.BaseSettings."""

    # No additional behaviour; env var loading not supported in stub.
