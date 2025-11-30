from __future__ import annotations

from typing import List, Dict

SYSTEM_PROMPT = (
    "You are Critic++. Given an exhibit and an extraction JSON, grade each field strictly. "
    "Output JSON array of objects: field, status (correct|incorrect|uncertain), rationale, better_evidence (quote or null), suggested_fix (concise or null)."
)


def messages(exhibit_text: str, extraction_json: str) -> List[Dict[str, str]]:
    user = f"EXHIBIT:\n<<<\n{exhibit_text}\n>>>\n\nEXTRACTION:\n{extraction_json}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
