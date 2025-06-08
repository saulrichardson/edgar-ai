"""Discoverer service.

Identifies potential fields (candidates) present in the documents.
"""

from __future__ import annotations

from typing import List

from ..interfaces import Document, FieldCandidate


_HARDCODED_FIELDS = [
    ("company_name", "Example Corp"),
    ("report_type", "10-K"),
    ("fiscal_year", "2023"),
]


def run(documents: List[Document]) -> List[FieldCandidate]:  # noqa: D401
    """Return deterministic field candidates regardless of input."""

    return [FieldCandidate(field_name=n, raw_value=v) for n, v in _HARDCODED_FIELDS]
