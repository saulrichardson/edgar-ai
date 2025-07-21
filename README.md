# Edgar-AI

**Automated, self-improving data extraction for SEC exhibits.**

Edgar-AI reads raw exhibits straight from EDGAR and turns them into clean,
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
                 Goal-Setter  (LLM)
                         │   determines `goal_id`
                         ▼
              ┌── Memory: schema? ──┐
              │                     │
        yes ──┘                     └── no
          │                           │
          ▼                           ▼
  Prompt-Builder (warm)         Schema Variants  (max / mini / bal)
          │                           │
          │                    ┌──────────────┐
          │                    │  Schema-Critic│◄─┐  evaluate each variant
          │                    └──────────────┘  │
          │                           │           │ scores
          │                    ┌──────────────┐  │
          │                    │ Schema-Refiner│──┤  improve each variant using
          │                    └──────────────┘  │  critic feedback
          │                           │           │
          │                    Referee  (uses ◄───┘  refined variants + scores
          │                    critic scores)
          │                           ▼
          └────────────── winning schema ─────────────┐
                                                     ▼
                                            Prompt-Builder
                                                     │
                                                     ▼
                                               Extractor
                                                     │  JSON rows + lineage
                                                     ▼
               ┌──────────────────────────┐
               │ Row-level Critic (LLM)   │
               └──────────────────────────┘
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
   `goal_id` matches the current document, we reuse it and jump **directly to
   extraction** – saving four LLM calls.  Otherwise we enter the cold-start
   path:

   **Schema Variants** – With the new prompt rules (observability, granularity,
   normal-form arrays), three candidate schemas are generated.

3. **Schema-Critic (per variant)** – Each candidate is scored against a set of
   design principles (normal-form modelling, observability, naming clarity…).
   The numeric scores are passed downstream so poor schemas can be rejected
   *before* any extraction work.

4. **Referee** – Combines its own reasoning with the Schema-Critic score
   vectors to pick the winner (or trigger a merge path). The champion is
   persisted in Memory.  See `docs/referee_merge_strategy.md` for optional
   merge logic.

5. **Prompt-Builder** – Converts the schema into a deterministic extraction
   prompt, surfacing any nested `json_schema` so the LLM knows when to emit
   arrays of objects.

6. **Extractor** – Large-context model returns structured JSON rows.  All
   prompts, model SHAs, and raw outputs are logged for provenance.

7. **Row-level Critic + Memory** – Another persona re-reads the document and grades each
   cell, referencing past mistakes stored in Memory.  Feedback is appended to
   the row’s lineage.

8. **Tutor** – When critic notes accumulate, the Tutor rewrites the schema or
   prompt section and submits a pull-request-style patch for human or automated
   approval (champion–challenger logic).

9. **Breaker** – Generates synthetic edge cases designed to fail current
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