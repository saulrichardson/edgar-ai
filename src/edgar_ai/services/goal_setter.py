"""Goal-Setter persona.

Pipeline unit = **one exhibit**.  Goal-Setter receives the full text of that
exhibit and returns a rich JSON objective containing:

* overview   – 1-2 sentences describing *why* we care about this exhibit.
* topics     – thematic areas (array of strings).
* fields     – candidate field names for extraction.

No simulation or stub paths: if the LLM gateway is mis-configured, an explicit
RuntimeError is raised so failures are visible.
"""

from __future__ import annotations

from typing import List

from ..llm import chat_completions, is_simulate_mode
from ..config import settings
from ..interfaces import Document

import logging
logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a research strategist charged with creating a comprehensive extraction schema that converts Edgar exhibits into a standardized tabular format capturing the full scope of information types common across similar conceptual exhibits.

Use internal chain-of-thought reasoning to reflect on:
  * The overarching goals of extraction and how they support a robust, reusable schema.
  * The thematic topics to include and why they matter.
  * The specific data fields to extract and their relevance to downstream analysis.

Do NOT include your reasoning in the response; return only the final JSON object.

Given the exhibit text below, return ONLY a JSON object with these keys:
  1. overview – A statement of the extraction purpose (up to 10 sentences) in the context of the tabular schema.
  2. topics   – An array of short phrases describing thematic areas to cover.
  3. fields   – An array of lowercase snake_case field names to extract from this exhibit.

EXAMPLE:
{
  "overview": "Extract contract parties and key loan terms to populate a unified loans dataset.",
  "topics": ["contract parties", "loan terms"],
  "fields": ["borrower", "lender", "loan_amount"]
}

Return ONLY valid JSON—no additional text or explanation.
"""

def _call_llm(snippet: str) -> str:
    rsp = chat_completions(
        model=settings.model_goal_setter,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": snippet},
        ],
        temperature=settings.goal_setter_temperature,
    )
    return rsp["choices"][0]["message"]["content"].strip()


def run(documents: List[Document]) -> str:  # noqa: D401
    """Return a goal sentence for *documents*."""

    if not settings.llm_gateway_url and not is_simulate_mode():
        raise RuntimeError("LLM gateway URL not configured; cannot run Goal-Setter")

    # Pipeline processes **one exhibit at a time**; pass the entire text to the
    # LLM so it can reason with full context.
    snippet = documents[0].text

    import json as _json

    for attempt in range(1, settings.goal_setter_max_retries + 1):
        raw = _call_llm(snippet)
        logger.debug("Goal-Setter raw output (attempt %d): %r", attempt, raw)

        try:
            goal = _json.loads(raw)
        except _json.JSONDecodeError:
            if attempt < settings.goal_setter_max_retries:
                snippet = (
                    snippet
                    + "\n\n⚠️ Your last response was not valid JSON. "
                    + "Please return only the JSON object in the format I asked."
                )
                continue
            raise RuntimeError(
                f"Goal-Setter failed to return JSON after {attempt} attempts; last output: {raw!r}"
            )

        if not isinstance(goal, dict):
            raise RuntimeError(f"Goal-Setter returned non-dict JSON: {goal!r}")

        required = ("overview", "topics", "fields")
        missing = [k for k in required if k not in goal]
        if missing:
            raise RuntimeError(f"Goal-Setter JSON missing required keys: {missing}")

        if not isinstance(goal.get("overview"), str):
            raise RuntimeError("Goal-Setter 'overview' must be a string")
        if not (isinstance(goal.get("topics"), list) and all(isinstance(t, str) for t in goal.get("topics", []))):
            raise RuntimeError("Goal-Setter 'topics' must be a list of strings")
        if not (isinstance(goal.get("fields"), list) and all(isinstance(f, str) for f in goal.get("fields", []))):
            raise RuntimeError("Goal-Setter 'fields' must be a list of strings")

        return goal
