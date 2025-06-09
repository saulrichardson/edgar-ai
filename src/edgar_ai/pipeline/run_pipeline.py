"""Orchestrate the extraction pipeline: schema selection → LLM extraction."""
from __future__ import annotations

from ..interfaces import Document
from ..memory import MemoryStore
from .choose_schema import choose_schema
from .extractor import extract


def run_pipeline(doc: Document, memory: MemoryStore) -> list[dict]:
    """Run the full pipeline: choose schema (cold or warm start), then extract rows."""
    schema = choose_schema(doc, memory)
    rows = extract(doc, schema)
    return rows