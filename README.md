# EdgarAI – North‑Star Specification (AI‑Maximal Version)

## 0. Fly‑Wheel First

EdgarAI is a **closed‑loop, self‑reinforcing fly‑wheel** that turns raw HTML SEC filings into perfectly structured tables—all with zero human rules.

**Core cycle (one pass)**

1. **Intake**  → raw HTML arrives.

2. **Goal‑Setter**  → agent infers the most valuable objective.

3. **Schema Synthesizer**  → drafts/updates a JSON schema.

4. **Prompt Builder**  → generates extraction instructions.

5. **Extractor**  → whole‑document reasoning fills the schema.

6. **Critic w/ Memory**  → scores output, recalls past errors.

7. **Tutor**  → rewrites prompt.

8. Back to **Intake**  with a stronger model—spinning faster with each filing and synthetic adversary.

The fly‑wheel autonomously **discovers goals, invents schemas, extracts, evaluates, and self‑improves**—hardening itself via synthetic edge cases and memory‑augmented critique.

> **North‑Star Outcome**: When any filing is fed into EdgarAI, it returns a perfect JSON/Parquet dataset plus a clickable lineage map—backed by a fly‑wheel that gets better every day with zero human tuning.

---

## 1. Core Principles

| #      | Principle                                                     | Impact                                                                                                                      |
| ------ | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **P1** | **Objective-First Autonomy**                                  | The agent chooses *what* to extract before it decides *how*, based purely on corpus patterns and its own observed objectives. |
| **P2** | **Prompt-Only Improvement**                                   | Prompts and schemas evolve purely via LLM-driven adjustments—no model weight updates or adapters.                            |
| **P3** | **Synthetic Edge-Case Generation**                            | A “Breaker” agent fabricates adversarial clauses so the system hardens itself before real docs change.                      |
| **P4** | **Hierarchical Memory & Ontology**                            | Vector memories roll up into a global knowledge graph that unifies concepts across domains.                                 |
| **P5** | **End-to-End Provenance & Explainability**                    | Every cell can be traced back to the exact HTML span, model SHA, prompt hash, critic score, and ontology node.             |
---

## 2. High‑Level Architecture

```
External API (optional) ─┐
                 ▼
            Explainer LLM  ◀──── Provenance Ledger & Ontology
                 ▲                          ▲
                 │                          │
 SEC HTML ▶ Intake ▶ Goal‑Setter ▶ Schema Synthesizer ▶ Prompt Builder ▶ Extractor ▶ Critic w/ Memory ▶ Tutor/RLHF ─┐
                 ▲                          ▲                                                             │        │
                 │                          └──────────── Vector Memory ◀──────── Breaker (Synthetic Docs) ┘        │
                 └──────────────────────────────────── Champion–Challenger Loop ─────────────────────────────────────┘
```

---

## 3. Data & Memory Fabric

| Layer                   | Stored Items                                                                                                                                                                 | Update Cadence | Technology (initial)                      |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | ----------------------------------------- |
| **Raw HTML Lake**       | Exact filing HTML                                                                                                                                                            | Streaming      | Object store (S3/GCS)                     |
| **Vector Memory (L0)**  | LLM‑addressable JSON shards of field‑values, critic notes, breaker samples                                                                                                   | Streaming      | Document store (Postgres JSONB / Elastic) |
| **Memory Digest (L1)**  | Nightly LLM summaries of L0 shards                                                                                                                                           | Nightly        | DocDB (Elastic)                           |
| **Ontology Graph (L2)** | Nodes = canonical concepts; edges = same‑as / broader‑than / causal                                                                                                          | On promotion   | Neo4j                                     |
| **Schema Registry**     | Immutable JSON schemas with **LLM‑generated names & alias pointers** (`champion`, `latest`, objective slugs); signed release docs; deprecated branches archived yet callable | On promotion   | Git repo                                  |
| **Provenance Ledger**   | Row‑level links: (doc id, span, model SHA, prompt SHA, critic score, ontology node)                                                                                          | Streaming      | Append‑only DB                            |

---

## 4. LLM Personas (System Prompts)

| Role                     | Purpose                                                                                                 | Key Prompt Directives                                                                                                     |                                                        |                                                                      |
| ------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------- |
| **Goal‑Setter**          | Invent or refine extraction objectives from filings + user logs                                         | "Propose the *single most valuable analytical goal* for these docs…"                                                      |                                                        |                                                                      |
| **Field‑Discoverer**     | List atomic facts in a passage                                                                          | "Return an array of {candidate\_field, snippet}."                                                                         |                                                        |                                                                      |
| **Schema‑Synthesizer**   | Cluster candidates → canonical JSON schema                                                              | "Group synonyms, assign types, minimise field count while maximising coverage."                                           |                                                        |                                                                      |
| **Prompt‑Writer**        | Turn schema → extraction template                                                                       | "Produce a deterministic JSON spec."                                                                                      |                                                        |                                                                      |
| **Extractor**            | Pull data from full HTML using template                                                                 | "Fill every field; output one JSON row per logical entity."                                                               |                                                        |                                                                      |
| **Critic (with Memory)** | Score rows, citing prior errors                                                                         | "Grade 0–1; retrieve past failures with similar wording; comment succinctly."                                             |                                                        |                                                                      |
| **Tutor**                | Reads critic comments and failed examples; outputs a revised JSON schema and updated extraction prompt. | "Using critic notes and failed examples, rewrite the JSON schema and extraction prompt to improve coverage and accuracy." |                                                        |                                                                      |
| **Breaker**              |                                                                                                         | **Breaker**                                                                                                               | Generate adversarial HTML that fools current extractor | "Craft plausible credit clauses that exploit extraction weaknesses…" |
| **Explainer**            | Answer any user question, referencing ontology & provenance                                             | "Respond conversationally; surface lineage, accuracy stats, caveats."                                                     |                                                        |                                                                      |

All personas run on the same frontier model (e.g., GPT‑4o‑128k) with role‑specific system messages.

---

## 5. Control Loop (Champion–Challenger, Fork‑and‑Vote)

```python
# simplified pseudocode for fork‑and‑vote
schemas = {"champion": SchemaChampion}
while True:
    batch_rows = {}
    batch_scores = {}

    # 1. run every active schema on the batch
    for name, schema in schemas.items():
        rows = Extractor(html_batch, schema)
        score, notes = Critic(html_batch, rows)
        batch_rows[name]   = rows
        batch_scores[name] = score
        persist(rows, score, notes)

    # 2. spawn a challenger fork if any score < DRIFT
    worst = min(batch_scores, key=batch_scores.get)
    if batch_scores[worst] < DRIFT_THRESHOLD:
        fork_schema, fork_prompt, lora = Tutor(low_score_notes[worst])
        schemas[f"fork_{uuid4()}"] = fork_schema

    # 3. voting: keep top‑K highest mean scores, prune the rest
    if len(schemas) > MAX_BRANCHES:
        top_k = sorted(batch_scores, key=batch_scores.get, reverse=True)[:MAX_BRANCHES]
        schemas = {name: schemas[name] for name in top_k}

    # 4. optional merge: if two schemas differ < epsilon, merge via Synthesizer
    similar_pairs = find_semantic_overlap(schemas.values())
    for a, b in similar_pairs:
        merged = SchemaSynthesizer.merge(a, b)
        schemas[f"merged_{uuid4()}"] = merged
```

*Promotion* writes Schema vX+1, model SHA, and release notes to the Registry and Ontology.

---

## 6. Synthetic Edge‑Case Generation

1. **Breaker** reads Vector Memory → learns common failure modes.
2. Generates hundreds of tricky clauses nightly (weird ratchets, nested definitions, OCR‑style noise).
3. These synthetic docs enter the same extraction loop; low scores amplify Tutor gradients.

Outcome: The system hardens *before* similar language appears in live SEC filings.

---

## 6A. Issue‑Critic (Optional Human Feedback)

*Purpose*: let domain experts supply structured error reports without directly editing schemas.

**Workflow**

1. **Submit** – via `/issue` endpoint or UI form: HTML snippet, current JSON, free‑text comment.
2. **Classify** *(LLM)* – tags as *missed field*, *incorrect value*, *new field proposal*, etc.
3. **Route** – stored in Vector Memory with `source="human"`; critic score weight × 2.
4. **Tutor Impact** – human‑flagged notes feed the same Tutor pipeline, accelerating schema/prompt or weight updates.

All Issue‑Critic entries are logged in the Provenance Ledger, so future lineage can show: “field fixed in v1.3 due to Issue‑Critic #42.”

---

## 6B. LLM‑Only Similarity & Governor‑Driven Decisions

*All decision gates previously described with numeric thresholds are now resolved by dedicated LLM agents—no hard‑coded τ, Δ, K, or M exist in the code base.*

### 6B.1 Field Equivalence (Ontology)

```text
System: “Are <Field A> and <Field B> semantically the same credit‑economics fact? Answer yes/no and one‑line why.”
```

* A **Yes** answer creates an alias edge in the ontology; answer is cached so the question is never re‑asked.

### 6B.2 Promotion, Pruning, Merging (Governor Agent)

The **Governor LLM** receives a JSON bundle every evaluation window:

```json
{
  "champion_score": 0.912,
  "challenger_score": 0.927,
  "critic_summary": "Challenger fixes margin‑floor parsing edge case…",
  "active_forks": ["vintage97", "ratchet_fix", "champion"]
}
```

It answers with:

```json
{
  "promote": true,
  "prune": ["vintage97"],
  "merge_candidates": [["ratchet_fix", "champion"]],
  "rationale": "Challenger materially improves… vintage97 now redundant…"
}
```

* **promote** → Fork‑Manager elevates the challenger to champion.
* **prune** → specified forks archived.
* **merge\_candidates** → passed to Schema‑Synthesizer to create a merged branch via LLM reasoning.

### 6B.3 Self‑Correction

Governor decisions and post‑decision critic scores are logged.  Tutor reviews missteps and fine‑tunes the Governor prompt/LoRA—fully autonomous policy improvement, still devoid of manual thresholds.

Outcome: every gate—field merge, fork creation, champion promotion, fork pruning, schema merge—relies on qualitative LLM judgement plus historical feedback, eliminating the need for any hand‑tuned numeric hyper‑parameters.

\---------------------|----------|-----------------|

The meta‑controller treats each parameter tuple as an **arm** in a contextual bandit; after every evaluation window it keeps the arm that maximises adjusted critic score.  No human ever sets or updates a number.

**Result**: Fork creation, voting, merging, and champion promotion are entirely LLM‑ and RL‑driven, with zero embeddings and zero hand‑tuned thresholds—yet still deliver provably higher critic scores over time.

---

## 7. Ontology Alignment Across Objectives

1. For every new field name the Schema‑Synthesizer proposes, the Ontology Manager queries the LLM:

   ```text
   System: "Are <Field A> and <Field B> semantically identical in context? Answer yes/no and one‑line why."
   ```
2. A **yes** answer creates a **same‑as** edge; a **no** answer spawns a new concept node.
3. The link is cached, so identical questions are never re‑asked.
4. Explainer uses the graph to answer cross‑domain queries ("show all `CoreRate` fields regardless of schema").

---

## 9. Success Metrics

| Theme              | Metric                            | Target |
| ------------------ | --------------------------------- | ------ |
| **Quality**        | Mean critic score (7‑day)         | ≥ 0.93 |
|                    | Breaker‑Real gap                  | < 3 pp |
| **Learning Speed** | Schema promotions w/out human     | ≥ 90 % |
| **Explainability** | External‑query clarification rate | < 15 % |
| **Reliability**    | Provenance trace success          | 100 %  |

---

## 10. Tech Stack (Initial)

| Layer                   | Choice (swappable)                   |
| ----------------------- | ------------------------------------ |
| LLM                     | GPT‑4o‑128k (OpenAI tenant)          |
| Streaming orchestration | Ray Serve (async DAG)                |
| Memory Store            | Postgres JSONB (or any document DB)  |
| Ontology store          | Neo4j 5                              |
| UI                      | Next.js + Dagre lineage viewer       |
| Monitoring              | Prometheus + Grafana + OpenTelemetry |

---

## 11. Roadmap Milestones

| Phase  | Scope                                            | Exit Criteria                                      |
| ------ | ------------------------------------------------ | -------------------------------------------------- |
| **M0** | Vertical slice on one filing, manual schema seed | Critic & Tutor improve score by ≥ 0.05 in one loop |
| **M1** | Fully autonomous schema discovery on 100 filings | Schema v0 promoted with ≥ 0.9 score                |
| **M2** | Add Breaker & LoRA tuning                        | Breaker gap < 3 pp over 1 week                     |
| **M3** | Ontology alignment across two objectives         | Cross‑schema query returns unified results         |
| **M4** | End‑to‑end provenance UI                         | Hover lineage working on > 95 % rows               |
| **M5** | Multi‑objective, continuous deployment           | No human edits > 30 days                           |

---

## 12. Extensibility & Future Work

* **Meta‑Controller**: RL agent that selects model sizes & temperatures.
* **Fine‑Grained User Feedback**: thumbs‑up/down directly updates critic memories.
* **Differential Privacy**: optional redaction layer for sensitive clauses before storage.

---

## 13. Summary

EdgarAI’s north‑star system:

1. **Discovers its own goals and schemas** from filings,
2. **Extracts** using entire‑document reasoning (no RAG),
3. **Judges** itself with a memory‑augmented critic,
4. **Learns** via RLHF and synthetic adversaries,
5. **Aligns** concepts into a live ontology,
6. **Explains** every output with interactive provenance.

With cost and latency de‑prioritised, every design choice maximises *accuracy, autonomy, and transparency*.  This document is the blueprint anyone can follow to build and extend the most AI‑forward EDGAR extraction engine imaginable.

