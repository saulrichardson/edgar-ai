from __future__ import annotations

from typing import List, Dict

from pipeline.context import ExhibitBundle

SYSTEM_PROMPT = (
    "You are Critic++. Given an exhibit and an extraction JSON, grade each field strictly. "
    "Output JSON array of objects: field, status (correct|incorrect|uncertain), rationale, better_evidence (quote or null), suggested_fix (concise or null)."
)


def build_user_message(bundle: ExhibitBundle, extraction_json: str) -> str:
    view = bundle.views[0]
    return f"EXHIBIT:\n<<<\n{view.text}\n>>>\n\nEXTRACTION:\n{extraction_json}"
