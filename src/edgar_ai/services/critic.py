"""Critic persona.

Current implementation: *stub* that emits an “info/looks good” note for every
row.

Target behaviour (LLM-powered):

1. Retrieve recent error memory for the same `schema` & `exhibit_type`.
2. Grade each row on a 0–1 scale, citing specific cell-level issues.
3. Optionally ingest human-filed issues as high-severity notes.

The output (`CriticNote`) feeds Tutor, Governor, and long-term Memory.
"""

from __future__ import annotations

from typing import List

from ..interfaces import CriticNote, Row


def run(rows: List[Row]) -> List[CriticNote]:  # noqa: D401
    """Return a benign note for each row."""

    return [CriticNote(message="Looks good", severity="info") for _ in rows]
