"""Discoverer service.

Identifies potential fields (candidates) present in the documents.
"""

from __future__ import annotations

from typing import List

from ..interfaces import Document, FieldCandidate
from ..config import settings
from ..llm import chat_completions, is_simulate_mode


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


_SYSTEM_PROMPT = """You are a field discovery assistant.\n\nGiven the full text of an SEC exhibit, list the most important data fields that should be extracted for structured analysis.\n\nRespond ONLY with a JSON array of lowercase snake_case field names (strings). No additional commentary.\n"""


def _discover_via_llm(doc_text: str) -> List[str]:  # noqa: D401
    rsp = chat_completions(
        model=settings.model_discoverer,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": doc_text[:8000]},  # truncate for token safety
        ],
        temperature=settings.discoverer_temperature,
    )

    import json as _json

    try:
        fields = _json.loads(rsp["choices"][0]["message"]["content"].strip())
    except Exception:
        # Fallback: treat entire content as single field name
        fields = ["misc_text"]

    # Ensure list[str]
    if not isinstance(fields, list):
        fields = [str(fields)]
    return [str(f) for f in fields if isinstance(f, str)]


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------


def run(documents: List[Document]) -> List[FieldCandidate]:  # noqa: D401
    """Return candidate fields for *documents*.

    • In simulate mode → deterministic triple (company_name, report_type, fiscal_year)
    • Otherwise → LLM-based discovery
    """

    if is_simulate_mode():
        stub = [
            ("company_name", "Example Corp"),
            ("report_type", "10-K"),
            ("fiscal_year", "2023"),
        ]
        return [FieldCandidate(field_name=n, raw_value=v) for n, v in stub]

    fields = _discover_via_llm(documents[0].text)
    return [FieldCandidate(field_name=f) for f in fields]
