"""Centralised configuration for the edgar_ai package.

In production this would read from environment variables or config files. For
now we expose a handful of constants and simple getters.
"""

from __future__ import annotations

import os


OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

# Batch size used by orchestrator.
BATCH_SIZE: int = int(os.getenv("EDGAR_AI_BATCH_SIZE", "8"))

# Database (unused in scaffold)
DATABASE_URI: str = os.getenv("DATABASE_URI", "sqlite:///:memory:")


def is_configured() -> bool:  # noqa: D401
    """Return *True* if all mandatory config values are present."""

    return OPENAI_API_KEY is not None
