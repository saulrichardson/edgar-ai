"""Prompt builder service using Jinja2 templates.

The template lives in *src/edgar_ai/prompts/extractor.jinja* so non-developers
can iterate on prompt wording without touching Python code.
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
    return Prompt(text=text, schema=schema)
