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

```text
                Raw HTML Filing
                         │
                         ▼
                    Intake
                         │
                         ▼
                 Goal-Setter (LLM)
                         │   determines `goal_id`
                         ▼
              ┌── Memory: schema? ──┐
              │                     │
        yes ──┘                     └── no
          │                           │
          ▼                           ▼
  Prompt-Builder (warm)        Schema Variants  (max / mini / bal)
          │                           │
          │                    Referee picks best
          │                           ▼
          └───────────── winning schema ────────────┐
                                                    ▼
                                           Prompt-Builder
                                                    │
                                                    ▼
                                              Extractor
                                                    │  JSON rows + lineage
                                                    ▼
                                                Critic
                                                    │  feedback
                                                    ▼
                                                Tutor
                                                    │  improved prompt / schema
                                                    └──► Memory   (learning loop)

        Breaker (adversarial docs) feeds synthetic edge cases into Intake →
```

Every pass through the fly-wheel makes the extractor **faster, broader, and
more accurate**—all by prompt evolution, never by re-training model weights.

---

## 2.  Step-by-Step Workflow

1. **Goal-Setter** – Reads only the exhibit text, decides the single most
   valuable analytical objective, and outputs a concise JSON goal.

2. **Schema lookup (warm-start)** – If Memory already holds a schema whose
   goal_id matches the current document, we reuse it and jump **directly to
   extraction** – saving three LLM calls.  Otherwise we enter the cold-start
   path:

   **Schema Variants** – With the new prompt rules (observability, granularity,
   normal-form arrays), three candidate schemas are generated.

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
