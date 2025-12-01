from __future__ import annotations

from typing import List, Dict

SYSTEM_PROMPT = (
    "You are Tutor. Given the current prompt, extraction, and critique, propose a challenger prompt update. "
    "Return either 'NO-CHANGE' if champion prompt is sufficient, or a revised prompt text. "
    "Keep improvements minimal, targeted to the critique findings."
)


def build_user_message(prompt_text: str, extraction: str, critique: str) -> str:
    return (
        "Current prompt:\n" + prompt_text + "\n\n"
        "Extraction:\n" + extraction + "\n\n"
        "Critique:\n" + critique + "\n\n"
        "Return revised prompt or NO-CHANGE."
    )
