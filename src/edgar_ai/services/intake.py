"""Intake service.

Transforms raw HTML strings into *Document* instances.
"""

from __future__ import annotations

from typing import List

from ..interfaces import Document


def run(html_batch: List[str]) -> List[Document]:  # noqa: D401
    """Convert raw HTML into *Document* objects.

    For the scaffold we deterministically assign a doc_id and pass the HTML
    through untouched.
    """

    documents: List[Document] = []
    for idx, html in enumerate(html_batch, start=1):
        doc = Document(doc_id=f"DOC-{idx}", html=html)
        documents.append(doc)
    return documents
