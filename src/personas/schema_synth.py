from __future__ import annotations

from typing import List, Dict

SYSTEM_PROMPT = (
    "You are Schema-Synth++. Emit three schemas for the same goal: lean, standard, strict. "
    "Use information-theoretic discipline: minimize redundancy, maximize mutual information with the goal, "
    "evidence-bound fields only, penalize vague fields. Output JSON array of three objects with keys: variant, rationale, risk, latency, "
    "fields (array of fields with name, type, required, description, evidence_rule). Return JSON only."
)


def build_user_message(goal: str, exhibit_sample: str) -> str:
    return (
        f"Goal: {goal}\n"
        f"Exhibit sample:\n<<<\n{exhibit_sample[:1800]}\n>>>\n"
        "Return JSON only."
    )


def messages(user_content: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
