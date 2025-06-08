"""Document provider service.

For the initial local-development phase, this service simply walks a directory
on disk and returns one *Document* per HTML/HTM file it finds.  Later this
module can be swapped for a network client that talks to a separate filing
micro-service.

Expected directory structure (loosely based on *sec-edgar-downloader* output)::

    filings_dir/
        full-submission.html
        ex10-1.htm
        ex99-1.htm

The *filings_dir* path is passed as the argument to :pyfunc:`run`.  Each file
generates a *Document* where ``doc_id`` is the filename and the exhibit type is
deduced from the filename (e.g. ``ex10`` → ``EX-10``).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from ..interfaces import Document

_EXHIBIT_REGEX = re.compile(r"ex(\d{1,2})(?:-(\d+))?", re.IGNORECASE)


def _guess_exhibit_type(file_name: str) -> str | None:
    """Best-effort exhibit type extraction from file name."""

    m = _EXHIBIT_REGEX.search(file_name)
    if m:
        num, sub = m.groups()
        # Preserve only the primary exhibit number (e.g., EX-10) for grouping
        return f"EX-{num}"
    if "full-submission" in file_name:
        return "FULL-SUBMISSION"
    return None


def run(filing_dir: str | Path) -> List[Document]:  # noqa: D401
    """Return a list of *Document*s for every HTML/HTM file in *filing_dir*."""

    root = Path(filing_dir).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(root)

    documents: List[Document] = []
    for path in root.iterdir():
        if path.suffix.lower() not in {".html", ".htm"}:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        exhibit_type = _guess_exhibit_type(path.name)
        documents.append(
            Document(
                doc_id=path.name,
                text=text,
                metadata={
                    "exhibit_type": exhibit_type,
                    "filing_dir": str(root),
                },
            )
        )

    if not documents:
        raise ValueError(f"No HTML files found in {root}")

    return documents
