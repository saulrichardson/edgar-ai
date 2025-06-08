"""In-memory raw data lake implementation for scaffolding purposes."""

from __future__ import annotations

from typing import Dict


_LAKE: Dict[str, str] = {}


def put(doc_id: str, html: str) -> None:
    _LAKE[doc_id] = html


def get(doc_id: str) -> str | None:
    return _LAKE.get(doc_id)


def all_docs() -> Dict[str, str]:  # noqa: D401
    return dict(_LAKE)
