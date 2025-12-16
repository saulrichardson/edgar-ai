from __future__ import annotations

import json
from typing import Any, Dict

SYSTEM_PROMPT = (
    "You are Prompt-Builder++. Given a goal and a candidate schema (JSON), craft a deterministic extraction prompt "
    "for an LLM Extractor.\n\n"
    "Requirements:\n"
    "- The extractor MUST return JSON only.\n"
    "- The output JSON must contain explicit fields with extracted values.\n"
    "- For every extracted field, also include evidence (quoted snippet) that supports the value.\n"
    "- If evidence is missing, set the value and its evidence to null.\n"
    "- Do not add commentary outside JSON.\n"
    "- Return the final extraction prompt text only."
)


def build_user_message(goal: Dict[str, Any], schema: Any, include_provenance: bool = False) -> str:
    goal_json = json.dumps(goal, ensure_ascii=False, indent=2)
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)

    provenance_block = ""
    if include_provenance:
        provenance_block = (
            "\n\nProvenance requirement: For every field, also emit <field>_provenance with "
            "{start_offset, end_offset, snippet}. Offsets are 0-based character positions into the EXHIBIT text; "
            "snippet is the exact quoted span used as evidence. If no evidence exists, set the provenance object to null."
        )

    return (
        "GOAL:\n"
        f"{goal_json}\n\n"
        "SCHEMA (JSON):\n"
        f"{schema_json}\n\n"
        f"Write the final extractor prompt.{provenance_block}"
    )
