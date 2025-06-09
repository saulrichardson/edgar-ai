"""Utilities for resolving the local *Edgar-AI* data directory.

The helper centralises the logic for deciding **where** on the local machine
all persistent artefacts (schemas, prompts, extracted rows, etc.) are stored.

Rules
-----
1. Respect the environment variable ``EDGAR_AI_HOME`` if it is set.
2. Otherwise default to the user’s home folder under ``~/.edgar_ai``.
3. Ensure the directory exists and is writable – create it (recursively) on
   first call.

The function returns a ``pathlib.Path`` instance so callers can easily create
sub-directories (e.g. ``get_data_dir() / "prompts"``).
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["get_data_dir"]


_ENV_VAR = "EDGAR_AI_HOME"
_DEFAULT_SUBDIR = ".edgar_ai"


def _resolve_path() -> Path:
    """Return the *candidate* data-dir path without creating it."""

    custom = os.environ.get(_ENV_VAR)
    if custom:
        return Path(custom).expanduser().resolve()

    return Path.home().joinpath(_DEFAULT_SUBDIR).resolve()


def get_data_dir() -> Path:  # noqa: D401
    """Return a writable directory path for all persistent Edgar-AI data.

    The directory is created (along with any missing parents) on first call.
    If the directory exists but is **not** writable, a ``PermissionError`` is
    raised so the caller can fail fast.
    """

    path = _resolve_path()

    # Ensure the directory hierarchy exists.
    path.mkdir(parents=True, exist_ok=True)

    # Basic writability check – try creating a temporary file.
    if not os.access(path, os.W_OK):
        raise PermissionError(f"Data directory is not writable: {path}")

    return path
