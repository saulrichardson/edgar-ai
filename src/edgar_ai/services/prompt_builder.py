"""Prompt-Builder persona.

Given a high-level extraction goal and schema, generate the optimal
function-calling prompt for the extractor LLM via the gateway.
"""

from __future__ import annotations

import json

from ..llm import chat_completions
from ..config import settings
from ..interfaces import Prompt, Schema

# ---------------------------------------------------------------------------
# Dynamic template with field enumeration
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a prompt-engineering assistant. Given a high-level extraction "
    "goal and a JSON schema, output the *SYSTEM* prompt that will be fed to "
    "another LLM. The SYSTEM prompt must:\n"
    "1. Restate the goal in one concise sentence.\n"
    "2. List every field in the schema with: name, JSON type, description and "
    "whether it is required. Use the exact field names.\n"
    "3. Instruct the model to respond via function-calling using the provided "
    "parameters schema.\n"
    "Return ONLY the final SYSTEM prompt text (no commentary).\n\n"
    "HIGH-LEVEL GOAL:\n{goal}\n\n"
    "SCHEMA (for your reference):\n{schema}\n"
)

def run(schema: Schema, goal: dict) -> Prompt:  # noqa: D401
    """Generate an extraction prompt for the provided goal and schema via LLM."""
    if not settings.llm_gateway_url:
        raise RuntimeError("LLM gateway URL not configured; cannot run Prompt-Builder")

    # Render goal and schema placeholders first
    input_content = _SYSTEM_PROMPT.format(
        goal=json.dumps(goal, ensure_ascii=False),
        schema=json.dumps({"fields": [f.model_dump() for f in schema.fields]}, ensure_ascii=False),
    )

    # Soft token-budget guardrail – rough estimate 1 token ≈ 4 characters.
    # If the prompt is grossly over the configured budget we truncate the
    # *goal* field first (rare), then abbreviate field descriptions.  This is
    # a best-effort safeguard rather than exact tiktoken counting to avoid the
    # heavyweight dependency.
    approx_token_count = len(input_content) // 4
    if approx_token_count > settings.prompt_builder_max_tokens:
        # Truncate goal text
        trimmed_goal = json.dumps(goal, ensure_ascii=False)[:2048] + "..."
        simplified_schema = {
            "fields": [
                {
                    "name": f.name,
                    "type": (f.json_schema or {}).get("type", "string"),
                    "description": (f.description[:120] + "..."),
                    "required": f.required,
                }
                for f in schema.fields
            ]
        }

        input_content = _SYSTEM_PROMPT.format(
            goal=trimmed_goal,
            schema=json.dumps(simplified_schema, ensure_ascii=False),
        )
    response = chat_completions(
        model=settings.model_prompt_builder,
        messages=[{"role": "user", "content": input_content}],
        temperature=settings.prompt_builder_temperature,
    )
    content = response["choices"][0]["message"]["content"].strip()

    # Build explicit fields section (name | type | description | required)
    lines = ["# === FIELD LIST (auto-generated) ==="]
    for f in schema.fields:
        field_type = (f.json_schema or {}).get("type", "string")
        req_flag = "required" if f.required else "optional"
        rationale_part = f" – {f.rationale}" if f.rationale else ""
        lines.append(f"- {f.name} ({field_type}, {req_flag}): {f.description}{rationale_part}")

    fields_block = "\n".join(lines)

    # Prepend to content so the extractor LLM sees it early.
    content = f"{fields_block}\n\n{content}"
    return Prompt(text=content, schema_def=schema)
