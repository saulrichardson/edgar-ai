"""Goal setter service.

In a full implementation this persona would evaluate documents and set high-
level extraction goals. For the scaffold we simply return a static string.
"""

from __future__ import annotations

from typing import List

from ..interfaces import Document


def run(documents: List[Document]) -> str:  # noqa: D401
    """Return a static goal based on provided documents."""

    # A deterministic stub goal.
    return "Extract key financial fields from 10-K filings."
