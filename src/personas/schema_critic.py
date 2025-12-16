from __future__ import annotations

import json
from typing import Any, Dict

from pipeline.context import ExhibitBundle


BASE_RULES = (
    "You are a Schema Critic. You will be given:\n"
    "- A goal (what the schema should enable)\n"
    "- A candidate schema (JSON)\n"
    "- An extraction output produced using that schema\n"
    "- The full source document\n\n"
    "Your job is to critique the schema as a representation, not to rewrite the entire pipeline.\n"
    "Be concrete: point to missing fields, redundant fields, ambiguous fields, or evidence failures.\n\n"
    "Output JSON only with keys:\n"
    "{\n"
    '  "verdict": "accept" | "revise" | "reject",\n'
    '  "strengths": string[],\n'
    '  "weaknesses": string[],\n'
    '  "suggested_changes": string[]\n'
    "}\n"
)


SYSTEM_PROMPTS: Dict[str, str] = {
    "informativeness": (
        BASE_RULES
        + "\nFocus: informativeness.\n"
        "- Does the schema capture the highest mutual information fields for the goal?\n"
        "- Are the fields sufficient to answer the goal robustly?\n"
        "- Are there missing high-signal variables?\n"
    ),
    "redundancy": (
        BASE_RULES
        + "\nFocus: redundancy / compression.\n"
        "- Are there duplicate or overlapping fields?\n"
        "- Could the schema be simplified without losing goal-relevant information?\n"
        "- Are names/descriptions unnecessarily verbose or repeated?\n"
    ),
    "evidence": (
        BASE_RULES
        + "\nFocus: evidence-boundness.\n"
        "- Are fields defined in a way that forces traceable evidence?\n"
        "- Did extraction hallucinate or fail to provide evidence?\n"
        "- Are any fields inherently not evidenceable from the document?\n"
    ),
    "robustness": (
        BASE_RULES
        + "\nFocus: robustness / generalization.\n"
        "- Would this schema work across similar documents with different formatting?\n"
        "- Are there brittle assumptions or layout-dependent fields?\n"
        "- Are type hints and definitions stable and unambiguous?\n"
    ),
}


def build_user_message(goal: Dict[str, Any], schema: Any, extraction_json: str, bundle: ExhibitBundle) -> str:
    view = bundle.views[0]
    goal_json = json.dumps(goal, ensure_ascii=False, indent=2)
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
    return (
        "GOAL:\n"
        f"{goal_json}\n\n"
        "CANDIDATE SCHEMA (JSON):\n"
        f"{schema_json}\n\n"
        "EXTRACTION OUTPUT (JSON text):\n"
        f"{extraction_json}\n\n"
        "SOURCE DOCUMENT:\n<<<\n"
        f"{view.text}\n"
        ">>>\n\n"
        "Return JSON only."
    )

