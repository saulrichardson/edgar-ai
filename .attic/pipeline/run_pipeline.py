"""Orchestrate the extraction pipeline: schema selection → LLM extraction."""
from __future__ import annotations

from ..interfaces import Document
# storage helper
from ..memory import FileMemoryStore
from .choose_schema import choose_schema
from .extractor import extract


def run_pipeline(doc: Document, memory: FileMemoryStore) -> list[dict]:
    """Run the full pipeline: choose schema (cold or warm start), then extract rows."""
    # ------------------------------------------------------------------
    # 1. Select a base schema (variant/referee flow) and persist in memory
    # ------------------------------------------------------------------
    schema = choose_schema(doc, memory)

    # ------------------------------------------------------------------
    # 2. Run Schema-Critic to obtain structured feedback
    # ------------------------------------------------------------------
    from ..services.schema_critic import run as schema_critic_run

    schema_id = f"schema_{len(memory.list_schema_records())}"
    critiques = schema_critic_run(schema_id, schema, doc)

    # ------------------------------------------------------------------
    # 3. Generate an *improved* schema that addresses the critiques
    # ------------------------------------------------------------------
    try:
        from ..services.schema_refiner import run as schema_refiner_run  # noqa: E402  local import

        refined_schema = schema_refiner_run(schema, critiques, doc)

        # Persist the refined schema if it differs and we have a gateway
        if refined_schema != schema:
            new_schema_id = f"schema_{len(memory.list_schema_records()) + 1}"
            memory.save_schema_record(new_schema_id, refined_schema, rationale="refined after critic")
            schema = refined_schema  # use for extraction
    except Exception:  # pragma: no cover – safe fallback if refiner unavailable
        pass

    # ------------------------------------------------------------------
    # 4. Extract rows using the (potentially refined) schema
    # ------------------------------------------------------------------
    rows = extract(doc, schema)

    # ------------------------------------------------------------------
    # 5. Row-level Critic for data quality feedback
    # ------------------------------------------------------------------
    from ..services.critic import run as critic_run

    _ = critic_run(rows)
    return rows
