# Fork & Merge Workflow in the LLM‑Orchestrated Pipeline

Your mental model is exactly right – there is one unified LLM‑orchestrated pipeline. When a document doesn’t fit the current goal/schema (as detected by Critic), we fork off to create a new goal and prompt, then route those docs back to the beginning under the new objective.

## 1. The Unified “Happy‑Path” Pipeline

```text
 ┌───────────────┐   candidate facts
 │  Goal-Setter  │
 └──────┬────────┘
        │   objective string
        ▼
 ┌───────────────┐   JSON Schema
 │ Field-Discover│────────────┐
 └──────┬────────┘             │
        ▼                      │
 ┌───────────────┐             │
 │ Schema-Synth  │──────────────┘
 └──────┬────────┘
        ▼   goal + schema
 ┌───────────────┐   extraction prompt
 │ Prompt-Writer │────────┐
 └──────┬────────┘        │
        ▼                 │ prompt
 ┌───────────────┐  rows  │
 │  Extractor    │────────┘
 └───────────────┘
```

All documents flow through this single path under the current goal.

## 2. Forking Back to the Top

| Phase       | Trigger                                            | Action                                                                                         |
|-------------|----------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Fork**    | Critic shows a document or subset consistently fails scoring | Goal-Setter generates a **new goal**; Schema‑Synthesizer and Prompt-Writer create a matching schema/prompt; re-enter pipeline top. |
| **Merge**   | Two goals reach ≥95 % critic score and overlap ≥90 % fields | Governor deprecates the redundant goal and merges schemas; duplicate processing avoided.       |
| **Back‑Fill** | A new champion prompt outperforms its predecessor by Δ≥ 0.05 | Historical filings are re-processed under the winning prompt to keep the ledger consistent.    |

## 3. Why This Matters

- **Single Code Path** – New or forked branches use the same intake → goal → discover → synth → prompt → extract → critic → tutor → governor workflow.  
- **Dynamic Adaptation** – The system autonomously spins up specialized goals/schemas when the current one proves a poor fit.  
- **Continuous Improvement** – Forking & merging ensure the pipeline refines itself over time without manual routing logic.

## 4. In a Nutshell

> **One pipeline + smart forking**: If a document “doesn’t fit” the current goal, the Critic triggers a fork (new goal + prompt), then documents loop back to the top. Governor then merges compatible branches later. This flywheel empowers Edgar‑AI to autonomously learn and evolve.