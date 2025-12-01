from __future__ import annotations

from pipeline.artifacts import PipelineState

SYSTEM_PROMPT = (
    "You are Governor. Decide champion vs challenger based on critiques and scores. "
    "Input: champion score, challenger score, champion critique, challenger critique. "
    "Output JSON with fields: decision (keep_champion|promote_challenger), rationale."
)


def build_user_message(champion_score: int, challenger_score: int, champion_crit: str, challenger_crit: str) -> str:
    return (
        f"Champion score: {champion_score}\n"
        f"Challenger score: {challenger_score}\n"
        "Champion critique:\n" + champion_crit + "\n\n"
        "Challenger critique:\n" + challenger_crit + "\n\n"
        "Return JSON: {\"decision\":..., \"rationale\":...}"
    )
