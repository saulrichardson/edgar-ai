from __future__ import annotations

import json
from typing import Any, Dict

from pipeline.context import ExhibitBundle


BASE_RULES = (
    "You are a Schema Proposer. Given a goal and a full document, propose the best extraction schema as JSON.\n\n"
    "The schema must define explicit fields (names + meaning) and be usable to drive deterministic extraction.\n"
    "You may choose any JSON structure (flat, nested objects, arrays) as needed.\n\n"
    "Hard requirements:\n"
    "- Output JSON only.\n"
    "- Every leaf field definition must include: a type hint, a human-readable description, and an evidence rule.\n"
    "- Favor fields that are observable and evidence-bound (no speculation).\n"
)


SYSTEM_PROMPTS: Dict[str, str] = {
    "max_information": (
        BASE_RULES
        + "\nInformation-theory focus:\n"
        "- Maximize mutual information between extracted fields and the goal.\n"
        "- Prefer high-signal fields even if they are harder, as long as evidence exists.\n"
        "- Avoid low-information boilerplate.\n"
    ),
    "min_redundancy": (
        BASE_RULES
        + "\nInformation-theory focus:\n"
        "- Minimize redundancy: do not include multiple fields that encode the same fact.\n"
        "- Prefer compressed representations and shared abstractions.\n"
        "- Penalize near-duplicate fields and verbose, overlapping descriptions.\n"
    ),
    "evidence_first": (
        BASE_RULES
        + "\nInformation-theory focus:\n"
        "- Treat evidence-boundness as a hard constraint.\n"
        "- Prefer fields with unambiguous textual anchors and stable wording.\n"
        "- If a high-value field is not reliably evidenced, exclude it.\n"
    ),
    "robust_general": (
        BASE_RULES
        + "\nInformation-theory focus:\n"
        "- Prefer schemas that will generalize across similar documents and formatting changes.\n"
        "- Avoid brittle fields tied to one-off layout or phrasing.\n"
        "- Prefer normalized, stable semantic fields over superficial presentation details.\n"
    ),
}


def build_user_message(goal: Dict[str, Any], bundle: ExhibitBundle) -> str:
    view = bundle.views[0]
    goal_json = json.dumps(goal, ensure_ascii=False, indent=2)
    return (
        "GOAL:\n"
        f"{goal_json}\n\n"
        "DOCUMENT:\n<<<\n"
        f"{view.text}\n"
        ">>>\n\n"
        "Return JSON only."
    )

