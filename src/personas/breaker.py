from __future__ import annotations

from pipeline.context import ExhibitBundle

SYSTEM_PROMPT = (
    "You are Breaker. Design 3-5 adversarial test cases that stress the current champion prompt for this goal. "
    "Each case should include a short description and the minimal fabricated snippet that would expose weaknesses. "
    "Return JSON array of objects: description, adversarial_snippet."
)


def build_user_message(goal: str, prompt_text: str) -> str:
    return (
        f"Goal: {goal}\n"
        f"Champion prompt:\n{prompt_text}\n\n"
        "Return JSON adversarial cases."
    )
