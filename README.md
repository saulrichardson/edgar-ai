# Edgar-AI

**Automated, self-improving data extraction for SEC exhibits.**

Edgar-AI reads raw HTML filings straight from EDGAR and turns them into clean,
query-ready tables—*without* hand-written regexes, templates, or routing rules.
An ensemble of LLM personas invents the goals, designs the schemas, extracts
the data, critiques itself, and learns from every document it touches.

> **Mission:** Make financial disclosure data instantly usable and keep the
> pipeline improving on its own, so analysts spend zero time on parsing and
> 100 % on insights.

---

## 1.  The Data Fly-Wheel

```
           ┌────────────── Intake ───────────────┐
           │   Raw EX-10 / EX-99 HTML Filing      │
           └────────────────┬────────────────────┘
                            │ text only
                            ▼
┌─────────── Goal-Setter ───────────┐
│ LLM decides *what* is worth       │  ← no hard-coded routes
│ extracting (creates `goal_id`)    │
└───────────┬───────────────────────┘
            │ objective JSON
            ▼
┌──────── Schema Variants ─────────┐        ┌── Breaker (adversarial drafts)
│ 3 candidate schemas (max/mini/bal)│       │   keep system on its toes
└───────────┬───────────────────────┘        └─────────────────────────────┐
            │                                synthetic docs                 │
            ▼                                                             ▼
┌───────────── Referee ─────────────┐
│ Picks best schema (or triggers     │
│ merge) – stored in Memory          │
└───────────┬───────────────────────┘
            │ winning schema
            ▼
┌───────── Prompt-Builder ──────────┐
│ Renders extraction prompt from     │
│ schema (incl. nested json_schema) │
└───────────┬───────────────────────┘
            │
            ▼
┌────────── Extractor ──────────────┐
│ LLM fills every field, returns     │
│ JSON rows                         │
└───────────┬───────────────────────┘
            │ rows + lineage meta
            ▼
┌──────────── Critic ───────────────┐
│ Scores accuracy, cites failures,   │
│ writes to Memory                   │
└───────────┬───────────────────────┘
            │ critic notes
            ▼
┌──────────── Tutor ────────────────┐
│ Uses critic feedback to propose    │  ← learning loop
│ prompt / schema improvements       │
└───────────┬───────────────────────┘
            │ updated artefacts
            └─────► back to Intake (next doc)
```

Every pass through the fly-wheel makes the extractor **faster, broader, and
more accurate**—all by prompt evolution, never by re-training model weights.

---

## 2.  Step-by-Step Workflow

1. **Goal-Setter** – Reads only the exhibit text, decides the single most
   valuable analytical objective, and outputs a concise JSON goal.

2. **Schema Variants** – With the new prompt rules (observability, granularity,
   normal-form arrays), three schemas are proposed.

3. **Referee** – Judges the variants against explicit criteria and saves the
   winner in a file-backed Memory store.  If none is adequate a merge path can
   be enabled (see `docs/referee_merge_strategy.md`).

4. **Prompt-Builder** – Converts the schema into a deterministic extraction
   prompt, surfacing any nested `json_schema` so the LLM knows when to emit
   arrays of objects.

5. **Extractor** – Large-context model returns structured JSON rows.  All
   prompts, model SHAs, and raw outputs are logged for provenance.

6. **Critic + Memory** – Another persona re-reads the document and grades each
   cell, referencing past mistakes stored in Memory.  Feedback is appended to
   the row’s lineage.

7. **Tutor** – When critic notes accumulate, the Tutor rewrites the schema or
   prompt section and submits a pull-request-style patch for human or automated
   approval (champion–challenger logic).

8. **Breaker** – Generates synthetic edge cases designed to fail current
   prompts, feeding them back into the pipeline and forcing continual
   hardening.

---

## 3.  Why This Works

| Principle | Effect |
|-----------|--------|
| **Observability-first schemas** | Every field can be answered from the exhibit alone; reduces hallucination. |
| **Normal-form modelling** | Repeating concepts become arrays with their own mini-schemas, enabling arbitrarily deep structures. |
| **Critic-Tutor feedback** | Objective, row-level scores drive prompt evolution; fixes propagate automatically. |
| **Adversarial Breaker** | Synthetic documents surface edge cases *before* production filings change. |
| **Champion–Challenger governance** | New prompts/schemas must outperform current champion before promotion, preventing regressions. |

---

## 4.  Jump In

```bash
# Install (editable) & run a quick extract
pip install -e .
python -m edgar_ai.cli extract path/to/exhibit.txt --verbose
```

See `docs/` for deep-dive design notes; start with `docs/architecture.md`.

Happy parsing! 🎉
