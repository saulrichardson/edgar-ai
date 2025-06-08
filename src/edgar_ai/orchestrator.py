"""Pipeline orchestrator.

`run_once` wires together the individual persona services so that the entire
pipeline can be executed with a single function call.
"""

from __future__ import annotations

from typing import List

from .interfaces import CriticNote, Document, GovernorDecision, Row

# Service imports
from .services import (
    breaker,
    critic,
    discoverer,
    extractor,
    goal_setter,
    governor,
    intake,
    prompt_builder,
    schema_synth,
    tutor,
)

# Storage helpers (not strictly required for scaffold but demonstrate use)
from .storage import ledger, raw_lake


def run_once(html_batch: List[str]) -> List[Row]:  # noqa: D401
    """Execute the full stub pipeline for a batch of HTML strings."""

    # 1. Intake: raw html -> Document
    documents: List[Document] = intake.run(html_batch)

    for doc in documents:
        raw_lake.put(doc.doc_id, doc.html)

    # 2. Goal setting (not used further but completes DAG)
    _ = goal_setter.run(documents)

    # 3. Discover field candidates
    candidates = discoverer.run(documents)

    # 4. Synth schema
    schema = schema_synth.run(candidates)

    # 5. Build prompt
    prompt = prompt_builder.run(schema)

    # 6. Extract rows
    rows: List[Row] = extractor.run(documents, prompt)

    for row in rows:
        if row.doc_id:
            ledger.add_row(row.doc_id, row)

    # 7. Critic feedback
    notes: List[CriticNote] = critic.run(rows)

    # 8. Tutor training loop (noop for scaffold)
    tutor.run(notes)

    # 9. Breaker tests (noop boolean)
    _ = breaker.run(rows)

    # 10. Governor decision
    decision: GovernorDecision = governor.run(rows, notes)

    # 11. Explainer (result ignored for now)
    _ = _publish_explanation(decision)

    return rows


def _publish_explanation(decision: GovernorDecision) -> str:
    """Generate and return user-facing explanation (currently stub only)."""

    from .services import explainer

    explanation = explainer.run(decision)
    return explanation
