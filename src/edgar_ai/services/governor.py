"""Governor service.

Makes a final decision on whether the pipeline results are acceptable.
"""

from __future__ import annotations

from typing import List

from ..interfaces import CriticNote, GovernorDecision, Row


def run(rows: List[Row], notes: List[CriticNote]) -> GovernorDecision:  # noqa: D401
    """Return a thumbs-up decision for the stub implementation."""

    decision_text = (
        "All rows accepted because the scaffold always produces valid data."
    )
    return GovernorDecision(approved=True, reasoning=decision_text)
