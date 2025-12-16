from __future__ import annotations

from typing import Dict, List

from pipeline.context import ExhibitBundle

SYSTEM_PROMPT = (
    "You are Goal-Setter. Read any business/legal exhibit and pick the single highest-value analytical "
    "goal for downstream extraction. The goal must be stable and reusable for routing similar future documents.\n\n"
    "Return JSON only with keys:\n"
    "{\n"
    '  "title": string,\n'
    '  "blueprint": string\n'
    "}\n\n"
    "Blueprint requirements:\n"
    "- Problem statement and what decision it supports\n"
    "- Target entities (what is being extracted)\n"
    "- Key facts to extract\n"
    "- Evidence expectations (what counts as justified)\n"
    "- Success criteria\n"
)


def build_user_message(bundle: ExhibitBundle) -> str:
    # default: use first view
    view = bundle.views[0]
    return (
        "Task: choose the best extraction goal for the exhibit below.\n\n"
        "EXHIBIT:\n<<<\n"
        f"{view.text}\n"
        ">>>\n\n"
        "Return JSON only."
    )


def messages(user_content: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
