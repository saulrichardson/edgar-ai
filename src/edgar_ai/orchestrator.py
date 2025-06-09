"""Pipeline orchestrator.

`run_once` wires together the individual persona services so that the entire
pipeline can be executed with a single function call.
"""

from __future__ import annotations

from typing import List

from .interfaces import CriticNote, Document, GovernorDecision, Row

# Service imports
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
    document_provider,
)

# Storage helpers (not strictly required for scaffold but demonstrate use)
from .storage import ledger, raw_lake


def run_once(html_batch: List[str]) -> List[Row]:  # noqa: D401
    """Execute the full stub pipeline for a batch of HTML strings."""

    # 1. Intake: raw html -> Document
    documents: List[Document] = intake.run(html_batch)

    for doc in documents:
        raw_lake.put(doc.doc_id, doc.text)

    # 2. Goal setting: determine the extraction objective for downstream prompts
    goal = goal_setter.run(documents)

    # 3. Discover field candidates
    candidates = discoverer.run(documents)

    # 4. Synth schema
    schema = schema_synth.run(candidates)

    # 5. Build prompt
    prompt = prompt_builder.run(schema, goal)

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


# Convenience wrapper -----------------------------------------------------


def run_for_filing(filing_dir: str) -> List[Row]:  # noqa: D401
    """Fetch exhibits for *filing_dir* and run the pipeline on each exhibit.

    The *filing_dir* corresponds to a folder on disk containing HTML / HTM
    files (e.g., output of *sec-edgar-downloader*).  The function returns the
    concatenated list of *Row*s produced for all exhibits.
    """

    exhibits = document_provider.run(filing_dir)

    rows: List[Row] = []
    for exhibit_doc in exhibits:
        rows.extend(run_once([exhibit_doc.text]))

    return rows



def _publish_explanation(decision: GovernorDecision) -> str:
    """Generate and return user-facing explanation (currently stub only)."""

    from .services import explainer

    explanation = explainer.run(decision)
    return explanation
