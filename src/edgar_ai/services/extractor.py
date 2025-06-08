"""Extractor service.

In production this would send the *Prompt* plus documents to OpenAI. For now
we return a single hard-coded *Row* regardless of input.
"""

from __future__ import annotations

from typing import List

from ..interfaces import Document, Prompt, Row


def run(documents: List[Document], prompt: Prompt) -> List[Row]:  # noqa: D401
    """Return one deterministic Row stub per document."""

    rows: List[Row] = []
    for doc in documents:
        row = Row(
            data={
                "company_name": "Example Corp",
                "report_type": "10-K",
                "fiscal_year": "2023",
            },
            doc_id=doc.doc_id,
        )
        rows.append(row)
    return rows
