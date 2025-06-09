"""Orchestrate the extraction pipeline: schema selection → LLM extraction."""
from __future__ import annotations

from ..interfaces import Document
# storage helper
from ..memory import FileMemoryStore
from .choose_schema import choose_schema
from .extractor import extract


def run_pipeline(doc: Document, memory: FileMemoryStore) -> list[dict]:
    """Run the full pipeline: choose schema (cold or warm start), then extract rows."""
    schema = choose_schema(doc, memory)
    rows = extract(doc, schema)
    return rows