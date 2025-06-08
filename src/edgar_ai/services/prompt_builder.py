"""Prompt-Builder persona.

Current state: **deterministic Jinja2 template**.

Road-map: replace with an LLM call so the model itself writes the extraction
prompt.  The future implementation will:

1. Receive a *high-level goal* string from Goal-Setter and a `Schema`.
2. Ask the LLM (via gateway) to craft the *best* function-calling prompt that
   fulfils that goal and schema.
3. Return that generated prompt.

Until the Critic/Tutor loop is online we keep the static template so the rest
of the pipeline remains runnable.
"""

from __future__ import annotations

from importlib import resources

from jinja2 import Template

from ..interfaces import Prompt, Schema


_TEMPLATE_PATH = resources.files("edgar_ai.prompts").joinpath("extractor.jinja")


def run(schema: Schema) -> Prompt:  # noqa: D401
    """Render the extraction prompt for the provided *schema*."""

    tpl_text = _TEMPLATE_PATH.read_text(encoding="utf-8")
    text = Template(tpl_text).render(fields=schema.fields)
    return Prompt(text=text, schema_def=schema)
