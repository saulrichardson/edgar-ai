"""Centralised runtime configuration using *pydantic-settings*.

Environment variables are automatically loaded and type-cast.  All variables
are prefixed with ``EDGAR_AI_`` to avoid collisions with system env-vars.

Defaults are suitable for local development; CI can override specific values
via standard environment variables, e.g. ``EDGAR_AI_BATCH_SIZE=16``.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Project-wide configuration model."""

    openai_api_key: str | None = None
    batch_size: int = 8
    database_uri: str = "sqlite:///:memory:"

    # meta – configure env-var prefix and optional .env loading
    model_config = SettingsConfigDict(
        env_prefix="EDGAR_AI_",  # environment vars like EDGAR_AI_BATCH_SIZE
        env_file=".env",  # load variables from a local .env if present
        env_file_encoding="utf-8",
    )


# Singleton instance to be imported across the codebase
settings = Settings()  # noqa: S303 – instantiation at import time is fine here


def is_configured() -> bool:  # noqa: D401
    """Return *True* if all mandatory configuration values are present."""

    return settings.openai_api_key is not None
