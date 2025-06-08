"""Prompt builder service.

Crafts the message that will be fed to the extractor persona / LLM.
"""

from __future__ import annotations

from ..interfaces import Prompt, Schema


def run(schema: Schema) -> Prompt:  # noqa: D401
    """Return a deterministic prompt embedding the supplied schema."""

    template = (
        "You are an information extraction agent. "
        "Return JSON objects with the following fields: {fields}. "
        "Respond with an array of objects."
    )
    prompt_text = template.format(fields=", ".join(schema.fields))
    return Prompt(text=prompt_text, schema=schema)
