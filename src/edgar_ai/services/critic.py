"""Critic service.

Reviews extracted rows and emits feedback notes.
"""

from __future__ import annotations

from typing import List

from ..interfaces import CriticNote, Row


def run(rows: List[Row]) -> List[CriticNote]:  # noqa: D401
    """Return a benign note for each row."""

    return [CriticNote(message="Looks good", severity="info") for _ in rows]
