from __future__ import annotations

from typing import List, Dict

from pipeline.context import ExhibitBundle

SYSTEM_PROMPT = (
    "You are Discoverer. From the exhibit and goal, propose <=12 candidate fields with names, type hints, and a one-line rationale. "
    "Return JSON array of objects: name, type_hint, rationale, evidence_hint. Focus on observable, high-information fields."
)


def build_user_message(goal: str, bundle: ExhibitBundle) -> str:
    view = bundle.views[0]
    return (
        f"Goal: {goal}\n"
        f"Exhibit:\n<<<\n{view.text}\n>>>"
    )
