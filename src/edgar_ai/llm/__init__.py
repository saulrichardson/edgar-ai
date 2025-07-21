"""Unified LLM access layer.

`edgar_ai.llm.chat_completions` is *the* function that the rest of the code
base should import when they need to talk to an LLM (or its local simulator).

It transparently routes the request to one of two back-ends:

1.  **Real gateway** – via the existing thin HTTP client
    ``edgar_ai.clients.llm_gateway`` when the environment variable
    ``EDGAR_AI_SIMULATE`` is *not* set to ``"1"``.

2.  **Simulate mode** – a deterministic, dependency-free stub located in
    ``edgar_ai.llm.simulate``.  Activate by exporting
    ``EDGAR_AI_SIMULATE=1`` before running the process (used by tests/CI).

All keyword arguments are forwarded unchanged, so callers can keep using the
OpenAI-style signature they already rely on.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

# Public re-export -----------------------------------------------------------

__all__ = [
    "chat_completions",
]


# ---------------------------------------------------------------------------
# Dynamic routing helper
# ---------------------------------------------------------------------------


def chat_completions(
    model: str,
    messages: List[Dict[str, str]],
    **kwargs: Any,
) -> Dict[str, Any]:  # noqa: D401
    """Unified entry-point for LLM chat completions – always routes to gateway."""

    from ..clients import llm_gateway  # lazy import to avoid cycles

    return llm_gateway.chat_completions(model=model, messages=messages, **kwargs)
