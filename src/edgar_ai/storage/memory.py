"""Lightweight in-memory key–value store representing vector or semantic memory."""

from __future__ import annotations

from typing import Any, Dict


_MEMORY: Dict[str, Any] = {}


def put(key: str, value: Any) -> None:
    _MEMORY[key] = value


def get(key: str) -> Any | None:  # noqa: D401
    return _MEMORY.get(key)


def clear() -> None:  # noqa: D401
    _MEMORY.clear()
