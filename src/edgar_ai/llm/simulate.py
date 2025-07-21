"""Deterministic, dependency-free simulator for LLM calls.

The goal is *not* to be smart—only to return syntactically correct responses
that unblock downstream parsing so that unit/integration tests can run
offline and without OpenAI credentials.

Strategy
--------
We inspect the incoming arguments to infer *which* persona is calling and
produce a minimal response structure that satisfies that persona’s parser.

Rules implemented (keep in sync with services):

1.  **Extractor** – presence of a ``tools`` argument means function-calling.
    We read the first tool’s JSON-Schema and return a single tool call with
    every field populated with ``"sim_<name>"`` values.

2.  **Goal-Setter** – if the system prompt contains the phrase
    ``"overview"`` **and** ``"topics"``, we return the canonical JSON goal.

3.  **Prompt-Builder** – otherwise, we treat it as a prompt builder request
    and return a dummy system prompt string.

You can extend this file whenever new personas require custom stubs.
"""

from __future__ import annotations

import json
import itertools
import uuid
from typing import Any, Dict, List


def _reply(content: str) -> Dict[str, Any]:
    """Return OpenAI-style response for plain text content."""

    return {
        "choices": [
            {
                "message": {
                    "content": content,
                }
            }
        ],
        "usage": {},
    }


def _reply_tool_call(arguments: Dict[str, Any], function_name: str = "submit_row") -> Dict[str, Any]:
    """Return response containing *one* tool_call."""

    return {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {
                            "id": str(uuid.uuid4()),
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": json.dumps(arguments, ensure_ascii=False),
                            },
                        }
                    ]
                }
            }
        ],
        "usage": {},
    }


def chat_completions(
    model: str,  # noqa: D401 – kept for compatibility
    messages: List[Dict[str, str]],
    **kwargs: Any,
) -> Dict[str, Any]:
    """Return a canned response based on *kwargs* heuristics."""

    # 1. Extractor path: presence of tools/function-calling
    tools = kwargs.get("tools")
    if tools:
        first_tool = tools[0]
        parameters = first_tool.get("function", {}).get("parameters", {})
        props = parameters.get("properties", {}) if isinstance(parameters, dict) else {}

        fake_row = {name: f"sim_{name}" for name in props.keys()}
        return _reply_tool_call(fake_row, function_name=first_tool.get("function", {}).get("name", "submit_row"))

    # Flatten all message contents for simple heuristics
    full_prompt = "\n".join(m["content"] for m in messages if m.get("content"))

    # 2. Goal-Setter / Schema-Variant detection: look for the three mandatory
    #    keys anywhere in the prompt (quotes optional).  This broader check
    #    covers both the original Goal-Setter and the newer schema variant
    #    generator used by *schema_variants.generate_variants*.
    lowered = full_prompt.lower()
    if all(k in lowered for k in ("overview", "topics", "fields")):
        # Distinguish between Goal-Setter (expects *array* of strings) and
        # Schema-Variant/Goal-Setter-v2 (expects *object* mapping) based on
        # the wording of the prompt.
        is_mapping = "object" in lowered and "mapping" in lowered

        if is_mapping:
            fields_value: Any = {
                "sim_field": {
                    "description": "Simulated description.",
                    "rationale": "Simulated rationale.",
                }
            }
        else:
            fields_value = ["sim_field1", "sim_field2", "sim_field3"]

        content = json.dumps(
            {
                "overview": "Simulated schema overview for offline tests.",
                "topics": ["sim_topic1", "sim_topic2"],
                "fields": fields_value,
            }
        )
        return _reply(content)

    # 3. Fallback – treat as prompt-builder or any other plain text
    return _reply("SIMULATED_PROMPT_TEXT")
