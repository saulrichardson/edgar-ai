"""Pipeline orchestrator.

`run_once` wires together the individual persona services so that the entire
pipeline can be executed with a single function call.
"""

from __future__ import annotations

from typing import List

from .interfaces import (
    CriticNote,
    Document,
    GovernorDecision,
    Row,
    FieldMeta,
    Schema,
)

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

# Simulate flag helper for conditional skips
from edgar_ai.llm import is_simulate_mode


def run_once(
    html_batch: List[str],
    *,
    verbose: bool = False,
    record_llm: bool = False,
) -> List[Row]:  # noqa: D401
    """Execute the pipeline for *html_batch*.

    Extra flags provide parity with the legacy `cli extract` implementation so
    that all functionality is preserved.
    """

    # 1. Intake: raw html -> Document
    documents: List[Document] = intake.run(html_batch)

    for doc in documents:
        raw_lake.put(doc.doc_id, doc.text)

    # 2. Goal setting: determine the extraction objective for downstream prompts
    goal = goal_setter.run(documents)

    # 3. Discoverer
    candidates = discoverer.run(documents)

    # 4. Schema synthesis (variant generation + referee happens inside the service)
    schema = schema_synth.run(candidates)

    # 5. Build prompt
    prompt = prompt_builder.run(schema, goal)


    # 6. Extract rows
    rows: List[Row] = extractor.run(documents, prompt)

    # Persist prompt & rows snapshots (best-effort; ignore failures)
    try:
        from edgar_ai.storage.snapshots import save_prompt, save_rows  # noqa: WPS433

        # Use simple stable hash based on schema JSON for directory grouping
        import json as _json, hashlib

        schema_hash = hashlib.sha256(
            _json.dumps([f.model_dump() for f in schema.fields], sort_keys=True).encode()
        ).hexdigest()[:12]

        save_prompt(prompt, schema_hash)
        for row in rows:
            if row.doc_id:
                save_rows(row.doc_id, [row])
    except Exception:  # pragma: no cover – non-fatal
        pass
    for row in rows:
        if row.doc_id:
            ledger.add_row(row.doc_id, row)

    if not is_simulate_mode():
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


def run_for_filing(
    filing_dir: str,
    *,
    verbose: bool = False,
    record_llm: bool = False,
    reset_memory: bool = False,
) -> List[Row]:  # noqa: D401
    """Fetch exhibits for *filing_dir* and run the pipeline on each exhibit.

    The *filing_dir* corresponds to a folder on disk containing HTML / HTM
    files (e.g., output of *sec-edgar-downloader*).  The function returns the
    concatenated list of *Row*s produced for all exhibits.
    """

    # Honour record flag globally via env var so services + llm layer pick it
    import os

    if record_llm:
        os.environ["EDGAR_AI_RECORD_SESSION"] = "1"
    if verbose:
        os.environ["EDGAR_AI_VERBOSE"] = "1"

    from pathlib import Path

    path_obj = Path(filing_dir).expanduser().resolve()

    if path_obj.is_dir():
        exhibits = document_provider.run(str(path_obj))
    else:
        # treat as single file (html/htm/txt)
        text = path_obj.read_text(encoding="utf-8", errors="ignore")
        exhibits = [Document(doc_id=path_obj.name, text=text, metadata={})]

    # Prepare memory store once per filing run (optional)
    from edgar_ai.memory import FileMemoryStore  # local import

    memory = FileMemoryStore()
    if reset_memory:
        # blunt reset – overwrite file with empty list
        try:
            memory._path.write_text("[]", encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass

    rows: List[Row] = []
    for exhibit_doc in exhibits:
        rows.extend(run_once([exhibit_doc.text], verbose=verbose, record_llm=record_llm))

    return rows



def _publish_explanation(decision: GovernorDecision) -> str:
    """Generate and return user-facing explanation (currently stub only)."""

    from .services import explainer

    explanation = explainer.run(decision)
    return explanation
