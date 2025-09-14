# Schema Evolution & Concept Promotion

This note explains **how newly–discovered concepts are promoted into the
official JSON Schema** without human intervention.  The mechanism applies
equally to material-contract exhibits (EX-10), earnings releases (EX-99), or
any future exhibit family.

> TL;DR – every raw field mention goes into a *candidates* table.  When the same
> concept appears often enough, Schema-Synthesiser automatically versions the
> schema and Prompt-Builder/Extractor start pulling the new column.  Historical
> filings are re-processed in the background.

---

## Data tables (Postgres JSONB)

| Table                | Purpose                                                         |
|----------------------|-----------------------------------------------------------------|
| `field_candidates`   | Raw (doc_id, goal_id, field_name, snippet, run_ts) from every run|
| `concept_backlog`    | Aggregated support counts awaiting promotion                    |
| `schemas`            | Versioned JSON Schemas (`schema_hash`, `goal_id`, `active`)      |
| `prompts`            | Champion/challenger prompt lineage                               |

SQL helper to create `concept_backlog` nightly:

```sql
INSERT INTO concept_backlog (goal_id, field_name, support_count)
SELECT goal_id, field_name, COUNT(*)
FROM   field_candidates
WHERE  run_ts > now() - interval '7 days'
GROUP  BY goal_id, field_name
HAVING COUNT(*) >= 3
ON CONFLICT (goal_id, field_name)
DO UPDATE SET support_count = concept_backlog.support_count + EXCLUDED.support_count;
```

Promotion threshold (`>= 10` support by default) is configurable per goal.

---

## Promotion pipeline

```text
field_candidates  ─┐ (nightly aggregate)
                   ▼
           concept_backlog  ──► Schema-Synth (promotion check)
                                │
                                ▼
                    schemas (v+1, active)
                                │
                                ▼
              Prompt-Builder → Extractor (new column)      
                                │
                                ▼
                      Back-fill job (historic docs)        
                                │
                                ▼
                    Critic (lenient → strict)              
```

1. **Accumulation** Field-Discoverer writes every candidate.
2. **Aggregation** Nightly SQL counts occurrences per exhibit family (`goal_id`).
3. **Backlog** When `support_count >= promotion_threshold` the concept is ready.
4. **Schema-Synth** Adds the new field(s), creating **Schema v+1** and marks it
   `active=true`.
5. **Prompt-Builder / Extractor** Use the new schema immediately in the next run.
6. **Back-fill** A background worker re-extracts rows for older filings so the
   ledger is consistent.
7. **Critic** Initially ignores missing values for the new column; after *M*
   runs enforces completeness.

---

## Configuration knobs

| Setting                | Default | Description                                    |
|------------------------|---------|------------------------------------------------|
| `promotion_threshold`  | 10      | # distinct docs that must surface the concept  |
| `aggregation_window`   | 7 days  | SQL window for support counting               |
| `backfill_batch_size`  | 100     | # filings re-processed per back-fill task      |

---

## Human oversight (optional)

* **Review queue** If required, promoted concepts can pause in a UI for human
  approval before schema activation.
* **Audit trail** `schemas` table stores creator (`system` vs `human`) and JSON
  diff so every field addition is traceable.

---

## Open TODOs

* Implement nightly aggregation job (`scripts/aggregate_candidates.py`).
* Add alembic migration stubs for the four tables.
* Extend Critic rubric to treat recently-promoted fields leniently for a
  grace-period.

Once these pieces are in place, the schema will grow organically as the system
encounters new terminology—no code changes or manual column edits required.
