from __future__ import annotations

import json
from typing import Any, Dict, List

from pipeline.context import ExhibitBundle

SYSTEM_PROMPT = (
    "You are Goal-Router. Your job is to route a document to an existing goal if it matches, "
    "otherwise declare that a new goal should be created.\n\n"
    "Principles:\n"
    "- Be conservative: only match an existing goal if it is clearly the same analytical objective.\n"
    "- Prefer stable goal identities over hyper-specific variations.\n"
    "- Do not invent new goals when an existing one fits.\n\n"
    "Output JSON only with keys:\n"
    "{\n"
    '  "decision": "match" | "new",\n'
    '  "goal_id": string | null,\n'
    '  "rationale": string\n'
    "}\n"
)


def build_user_message(bundle: ExhibitBundle, goals: List[Dict[str, Any]]) -> str:
    view = bundle.views[0]
    goals_json = json.dumps(goals, ensure_ascii=False, indent=2)
    return (
        "KNOWN GOALS:\n"
        f"{goals_json}\n\n"
        "DOCUMENT:\n<<<\n"
        f"{view.text}\n"
        ">>>\n\n"
        "Return JSON only."
    )

