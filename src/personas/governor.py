from __future__ import annotations

import json
from typing import Any, Dict, List

from pipeline.context import ExhibitBundle

SYSTEM_PROMPT = (
    "You are Governor. Decide which candidate schema should become the champion for this goal.\n\n"
    "You will receive:\n"
    "- The goal (stable, used for routing)\n"
    "- The full document\n"
    "- A set of candidate schemas (JSON)\n"
    "- A set of critic council outputs per candidate\n\n"
    "Principles:\n"
    "- Treat critic dimensions as co-equal unless there is a clear evidence failure.\n"
    "- Prefer schemas that are both informative for the goal and evidence-bound.\n"
    "- Prefer simpler schemas when they preserve goal-relevant information (compression/MDL intuition).\n"
    "- If all candidates are weak, choose the least-bad and explain what to fix next.\n\n"
    "Output JSON only with keys:\n"
    "{\n"
    '  "champion_candidate_id": string,\n'
    '  "rationale": string,\n'
    '  "next_improvements": string[]\n'
    "}\n"
)


def build_user_message(goal: Dict[str, Any], candidates: List[Dict[str, Any]], bundle: ExhibitBundle) -> str:
    view = bundle.views[0]
    goal_json = json.dumps(goal, ensure_ascii=False, indent=2)
    candidates_json = json.dumps(candidates, ensure_ascii=False, indent=2)
    return (
        "GOAL:\n"
        f"{goal_json}\n\n"
        "CANDIDATES (schemas + council outputs):\n"
        f"{candidates_json}\n\n"
        "DOCUMENT:\n<<<\n"
        f"{view.text}\n"
        ">>>\n\n"
        "Return JSON only."
    )
