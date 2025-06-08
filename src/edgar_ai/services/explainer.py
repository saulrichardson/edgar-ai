"""Explainer service.

Produces a summary of the governor's decision.
"""

from __future__ import annotations

from ..interfaces import GovernorDecision


def run(decision: GovernorDecision) -> str:  # noqa: D401
    """Return a human-readable explanation of the decision."""

    if decision.approved:
        return "Pipeline execution approved."
    return "Pipeline execution rejected."
