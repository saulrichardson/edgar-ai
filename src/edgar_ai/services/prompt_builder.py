"""Prompt-Builder persona.

Given a high-level extraction goal and schema, generate the optimal
function-calling prompt for the extractor LLM via the gateway.
"""

from __future__ import annotations

import json

from ..clients import llm_gateway
from ..config import settings
from ..interfaces import Prompt, Schema

_SYSTEM_PROMPT = """You are a prompt engineering assistant. Given a high-level extraction goal and a JSON schema that defines the fields to extract, generate a system prompt to instruct an LLM to extract the specified fields from a document using OpenAI function-calling.
Return ONLY the final prompt text (no commentary).

GOAL:
{goal}

SCHEMA:
{schema}
"""

def run(schema: Schema, goal: dict) -> Prompt:  # noqa: D401
    """Generate an extraction prompt for the provided goal and schema via LLM."""
    if not settings.llm_gateway_url:
        raise RuntimeError("LLM gateway URL not configured; cannot run Prompt-Builder")

    input_content = _SYSTEM_PROMPT.format(
        goal=json.dumps(goal, ensure_ascii=False),
        schema=json.dumps({"fields": schema.fields}, ensure_ascii=False),
    )
    response = llm_gateway.chat_completions(
        model=settings.model_prompt_builder,
        messages=[{"role": "user", "content": input_content}],
        temperature=settings.prompt_builder_temperature,
    )
    content = response["choices"][0]["message"]["content"].strip()
    return Prompt(text=content, schema_def=schema)
