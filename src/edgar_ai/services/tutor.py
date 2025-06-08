"""Tutor persona.

Goal: use Critic feedback to produce an *improved* extraction prompt (a
"challenger") which will compete against the current "champion" in the next
run.  Governor decides which prompt wins.

Current status: **noop** – placeholder.
Next steps:
1. Build an instruction prompt: "Here is the current prompt and critic notes;
   rewrite the prompt to fix the issues."  Send via LLM gateway.
2. Store the challenger prompt in the ledger with a unique hash.
3. Governor compares average critic scores over a window and may promote.
"""


from typing import List

from ..interfaces import CriticNote


def run(notes: List[CriticNote]) -> None:  # noqa: D401
    """A no-op stub."""

    # Intentionally do nothing – returns None.
