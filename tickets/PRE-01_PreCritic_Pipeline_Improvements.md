Ticket: PRE-01 – Pre-Critic Pipeline Hardening

Context
-------
Before the self-learning loop (Critic ▸ Tutor ▸ Governor) can reliably judge
quality, the *front half* of the pipeline (Intake → Goal-Setter → Discoverer
→ Schema-Synth → Prompt-Builder → Extractor) must be robust, deterministic
where possible, and cost-efficient.  This ticket consolidates all remaining
gaps identified during the design review.

Checklist of Work
-----------------

### Intake
1. Preserve real document identity (accession #, filename) in `Document.doc_id` & `metadata`.
2. Strip boiler-plate HTML, normalise unicode, collapse whitespace.
3. Detect language; store `metadata['language']`.
4. Compute SHA-256 checksum + raw length; persist for duplicate detection.

### Goal-Setter
5. Cache output keyed by document checksum to avoid repeat LLM calls.
6. Add `confidence` score; abort pipeline early if below threshold.
7. Rank `topics` and `fields` or flag "required" vs "optional".
8. Implement self-consistency loop (n stochastic runs → majority vote).

### Discoverer
9. Accept `goal` arg and return enriched `FieldCandidate` (description, example, confidence).
10. Chunk long exhibits (> context window) with overlap; union results.
11. Validate candidate names (snake_case, ≤ 4 tokens, no punctuation).
12. Skip discovery when a schema satisfying the goal already exists in memory.
13. Optionally 3-way self-consistency voting to improve recall.

### Schema-Synth
14. Generate multiple schema variants (minimalist/maximalist/balanced).
15. Infer JSON types from candidate examples.
16. Mark field `required` when confidence ≥ 0.8.
17. Add regex patterns, enums, unit annotations where obvious.
18. Embed `goal_hash` & per-field provenance/rationale in `Schema`.
19. Persist *all* variants; return referee winner only.

### Prompt-Builder
20. Insert domain-specific few-shot examples.
21. Calculate real token count with `tiktoken` and truncate intelligently.
22. Cache prompts keyed by `(goal_hash, schema_hash)`.

### Extractor
23. Validate rows via `jsonschema` (types, enums, patterns, required).
24. Support multi-row extraction when schema type == array.
25. Post-process: normalise dates (ISO-8601), numbers (float), trim strings.
26. Add exponential back-off & verbose error surfacing on failed gateway calls.
27. Persist `schema_id` along with each `Row` for historic error lookup.

### Cross-cutting (before Critic)
28. Replace in-memory `ledger` with durable store (SQLite/Parquet).
29. Expose timing, token, and cost metrics via Prometheus counters.
30. Centralise caching layer (fs/Redis) for Goal-Setter & Prompt-Builder.
31. Structured error handling: if any pre-critic step hard-fails, short-circuit run and mark filing for manual triage.

Acceptance Criteria
-------------------
* Running `python -m edgar_ai.cli extract <path> --simulate` remains green.
* Live mode processes ≥ 20 filings without hitting unhandled exceptions.
* Metrics endpoint (/metrics) shows per-persona counters.
* Duplicate filings reuse cached goal/prompt outputs (verify via logs or cost drop).

Notes
-----
This ticket serves as an umbrella; individual sub-tasks should be broken out
into atomic tickets (DISC-0x, SCH-0x, MEM-0x, etc.) tracked in the `tickets/`
directory.

