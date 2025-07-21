"""Schema Refiner – improve a JSON extraction schema using Schema-Critic feedback.

This lightweight helper takes the **original** schema plus a list of
`SchemaCritique` objects (output from *schema_critic.run*) and asks the LLM to
return an **improved** version that addresses the critiques.  When the LLM
gateway is not configured (e.g. unit-test or offline mode) the function simply
returns the incoming schema unchanged so callers can safely rely on it without
extra guards.
"""

from __future__ import annotations

import json
from typing import List, Dict, Any

from ..config import settings
from ..llm import chat_completions, is_simulate_mode
from ..interfaces import Document, SchemaCritique


_SYSTEM_PROMPT = (
    "You are a senior data-architect tasked with **refining** an existing JSON "
    "extraction schema.  The current schema has been reviewed by an autonomous "
    "Schema-Critic who produced the critiques listed below.  Return a new, "
    "improved schema that *fully addresses* the critic's feedback while "
    "preserving field names whenever possible.\n\n"
    "Guidelines:\n"
    "• Keep the response strictly valid JSON – no markdown fences.\n"
    "• Preserve any field already satisfactory unless the critique suggests a "
    "  modification or removal.\n"
    "• If you introduce new repeating structures, add a `json_schema` entry.\n"
    "• Maintain the top-level keys: overview, topics, fields (list of objects).\n"
)


def _format_critiques(critiques: List[SchemaCritique]) -> str:  # noqa: D401 – helper
    """Return a printable bullet list summarising critic feedback."""

    if not critiques:
        return "(no critic feedback)"

    bullet_lines = [
        f"- {c.principle} (score {c.score:.2f}): {c.message}" for c in critiques
    ]
    return "\n".join(bullet_lines)


def run(
    schema: Dict[str, Any],
    critiques: List[SchemaCritique],
    doc: Document,
) -> Dict[str, Any]:  # noqa: D401
    """Return an *improved* schema that incorporates *critiques*.

    If the LLM gateway URL is not configured we fall back to returning the
    original *schema* so downstream code continues to work in offline mode.
    """

    # Fast exit if gateway missing – useful for unit-tests without network.
    if not settings.llm_gateway_url:
        return schema

    user_msg = (
        "CURRENT SCHEMA:\n" + json.dumps(schema, ensure_ascii=False, indent=2) + "\n\n"  # original schema
        "CRITIC FEEDBACK:\n" + _format_critiques(critiques) + "\n\n"
        "EXHIBIT EXCERPT (for grounding, truncated):\n" + doc.text[:4000]
    )

    # If simulate mode active, always return original schema unchanged so that
    # deterministic test runs stay stable.
    if is_simulate_mode():
        return schema

    resp = chat_completions(
        model=settings.model_goal_setter,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=settings.goal_setter_temperature,
    )

    raw = resp["choices"][0]["message"].get("content", "").strip()

    # Strip optional ```json fences if present
    import re

    m = re.match(r"```(?:json)?\s*(.*)\s*```", raw, flags=re.S | re.I)
    if m:
        raw = m.group(1)

    try:
        return json.loads(raw)
    except Exception:  # pragma: no cover – return original on parse failure
        return schema
