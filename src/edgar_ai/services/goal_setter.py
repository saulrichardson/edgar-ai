"""Goal-Setter persona – selects the highest-value extraction objective.

Modes
-----
1. **Live** (`settings.simulate == False` *and* `llm_gateway_url` is set)
   • Calls the LLM Gateway and returns the model’s sentence.
2. **Simulation** (`settings.simulate == True`)
   • Constructs a deterministic yet plausible goal from exhibit metadata so
     tests/dev can run offline.
3. **Stub** (fallback)
   • Returns a generic catch-all objective.
"""

from __future__ import annotations

from typing import List

from ..clients import llm_gateway
from ..config import settings
from ..interfaces import Document

_SYSTEM_PROMPT = """You are a research strategist.

Given the exhibit text below, return ONLY a JSON object with these keys:
  1. overview – 1-2 sentences summarising the high-level extraction purpose.
  2. topics   – array of short phrases describing thematic areas to cover.
  3. fields   – array of lowercase snake_case field names you expect to extract.

EXAMPLE:
{
  "overview": "Extract contract parties and key loan terms…",
  "topics": ["contract parties", "loan terms"],
  "fields": ["borrower", "lender", "loan_amount"]
}

Return ONLY valid JSON.
"""

_GENERIC_GOAL = {
    "overview": "Extract key facts from the document.",
    "topics": [],
    "fields": [],
}


def _simulate_goal(docs: List[Document]) -> str:
    """Return a deterministic goal based on exhibit_type metadata."""

    exhibit_type = docs[0].metadata.get("exhibit_type", "").upper()

    if exhibit_type.startswith("EX-10"):
        return {
            "overview": "Extract contract parties, effective date and dollar amount from material contracts.",
            "topics": ["contract parties", "effective date", "contract value"],
            "fields": [
                "borrower",
                "lender",
                "effective_date",
                "contract_value",
            ],
        }
    if exhibit_type.startswith("EX-99"):
        return {
            "overview": "Extract headline financial metrics and year-over-year deltas from the earnings press release.",
            "topics": ["revenue", "EPS", "YoY"],
            "fields": ["revenue", "eps", "revenue_yoy", "eps_yoy"],
        }
    return _GENERIC_GOAL


def _call_llm(snippet: str) -> str:
    rsp = llm_gateway.chat_completions(
        model=settings.model_goal_setter,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": snippet},
        ],
        temperature=0.3,
    )
    return rsp["choices"][0]["message"]["content"].strip()


def run(documents: List[Document]) -> str:  # noqa: D401
    """Return a goal sentence for *documents*."""

    if settings.simulate:
        return _simulate_goal(documents)

    if not settings.llm_gateway_url:
        return _GENERIC_GOAL

    snippet = "\n\n".join(d.text[:2000] for d in documents[:2])

    try:
        raw = _call_llm(snippet)
        import json as _json

        try:
            return _json.loads(raw)
        except _json.JSONDecodeError:  # pragma: no cover – fall back if not JSON
            return {"overview": raw, "topics": [], "fields": []}
    except Exception:  # pragma: no cover
        return _GENERIC_GOAL
