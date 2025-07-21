# Edgar-AI Architecture – LLM-First, Self-Evolving

This document captures the **design intent** behind every component so that
future contributors understand *why* the code looks the way it does and *how*
the system is expected to learn without ongoing human intervention.

> TL;DR — Edgar-AI is objective-first.  An LLM decides **what** is valuable to
> extract, then other LLM personas figure out **how** to extract it, judge the
> results, and improve themselves.  Humans set an initial seed objective and
> may raise issues, but the fly-wheel owns everything else.

---

## Component lifecycle

```text
 ┌───────────────┐
 │  Goal-Setter  │  ⇠─── (first & only human seed)
 └──────┬────────┘
        │   objective string
        ▼
 ┌───────────────┐   candidate facts
 │ Field-Discover │────────────┐
 └──────┬────────┘             │
        ▼                      │
 ┌───────────────┐   JSON Schema│
 │ Schema-Synth  │──────────────┘
 └──────┬────────┘
        ▼   goal + schema
 ┌───────────────┐   extraction prompt
 │ Prompt-Writer │────────┐
 └──────┬────────┘        │
        ▼                 │ prompt
 ┌───────────────┐  rows  │
 │  Extractor    │────────┘
 └──────┬────────┘
        ▼                 ▲
 ┌───────────────┐ notes  │
 │    Critic     │────────┘
 └──────┬────────┘
        ▼
 ┌───────────────┐ challenger prompt
 │    Tutor      │─────────────────┐
 └──────┬────────┘                 │
        ▼                          │
 ┌───────────────┐ promote/rollback│
 │   Governor    │─────────────────┘
 └───────────────┘
```

All arrows represent **LLM reasoning steps** executed via the `/v1/chat/completions`
endpoint of the **LLM Gateway**.  No module calls vendor SDKs directly.

### Key principles

1. **Objective-First** – Goal-Setter decides *what* to extract.  Nothing is
   hard-coded.
2. **Self-Evolving** – Critic → Tutor → Governor loop refines prompts and
   schemas without humans.
3. **Fork & Merge** – Goals/schemas fork when recurring critic failures reveal
   sub-domains (e.g., credit agreements vs. employment agreements) and merge
   when they can be satisfied together.
4. **Back-Correction** – When a new champion prompt significantly outperforms
   its predecessor, historical filings are re-processed to keep the ledger
   consistent.

---

## Fork / Merge lifecycle

| Phase | Trigger                                             | Action by LLM personas                      |
|-------|-----------------------------------------------------|---------------------------------------------|
| Fork  | Critic shows persistent low score for a subset      | Goal-Setter spawns **new goal**; Schema-Synthers create a schema just for that branch. |
| Merge | Two goals reach ≥ 95 % critic score and overlap ≥ 90 % fields | Governor deprecates redundant goal; rows re-tagged. |
| Back-fill | New champion prompt improves score by Δ≥0.05     | Back-fill job re-extracts old filings; ledger supersedes rows. |

Implementation artifacts:

* `goals` table — `goal_id`, `exhibit_type`, `status{active,deprecated}`
* `schemas` table — `schema_hash`, `goal_id`
* `prompts` table — `prompt_hash`, `goal_id`, `parent_hash`, `avg_score`

These tables live in Postgres; services access them via helpers in
`src/edgar_ai/storage/`.

---

## Human-in-loop touch-points

1. **Seed Goal** – A one-time sentence: "Extract essential terms from material
   contracts."  After that, Goal-Setter evolves it.
2. **Issue Critic** – A human may flag an incorrect row; the note is injected
   into the Critic stream with `severity='human_high'`.  Governor treats these
   as blocking failures until resolved.

Everything else is autonomous.  Even schema evolution happens without code
changes.

---

## Open TODOs for full autonomy

| Component          | Status | Next step |
|--------------------|--------|-----------|
| Goal-Setter        | LLM    | Generate JSON goal via LLM based on exhibit text |
| Field-Discoverer   | LLM    | Generate field candidates (`name`, `description`, `rationale`) via LLM (schema_variants) |
| Schema-Synthesizer | LLM    | Refine and merge candidates into JSON schema via LLM (schema_variants referee/merge_referee) |
| Schema-Critic      | LLM    | Score each candidate schema against design principles before selection |
| Prompt-Writer      | LLM    | Generate extraction prompt via LLM based on goal and schema |
| Extractor          | LLM    | Extract via function-calling and parse real `tool_calls` JSON into rows |
| Row-level Critic   | STUB   | LLM grades rows, pulls memory    |
| Tutor              | NOP    | LLM rewrites challenger prompt   |
| Governor           | STUB   | LLM promotes based on critic avg |
| Breaker            | STUB   | LLM crafts adversarial filings   |

Contributors should update this table whenever a stub is replaced by a real
LLM call.  The **goal is 100 % LLM-reasoned data pipeline** except for the two
explicit human touch-points above.
