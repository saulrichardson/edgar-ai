"""LLM-driven extraction: render Jinja prompt, invoke extractor LLM, parse rows."""
from __future__ import annotations

import json

from jinja2 import Environment, FileSystemLoader

from ..clients import llm_gateway
from ..config import settings
from ..interfaces import Document

# Configure Jinja2 environment to load prompt templates
env = Environment(loader=FileSystemLoader("src/edgar_ai/prompts"))
template = env.get_template("extractor.jinja")


def extract(doc: Document, schema: dict) -> list[dict]:
    """Extract rows matching the schema from the given document via the LLM."""
    # Accept either rich meta objects or plain strings
    raw_fields = schema.get("fields", [])
    if raw_fields and isinstance(raw_fields[0], dict) and "name" in raw_fields[0]:
        fields = raw_fields  # already list[dict]
    else:
        fields = [{"name": str(f), "description": ""} for f in raw_fields]

    system_prompt = template.render(fields=fields)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": doc.text},
    ]
    response = llm_gateway.chat_completions(
        model=settings.model_extractor,
        messages=messages,
    )
    content = response["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return []