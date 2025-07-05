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

    from ..services.schema_critic import run as schema_critic_run

    schema_id = f"schema_{len(memory.list_schema_records())}"
    _ = schema_critic_run(schema_id, schema, doc)

    rows = extract(doc, schema)

    from ..services.critic import run as critic_run

    _ = critic_run(rows)
    return rows