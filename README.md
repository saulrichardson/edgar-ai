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
7. **Tutor / RLHF**  → rewrites prompt, tweaks LoRA weights.
8. **Fork‑and‑Vote loop**  → best schema becomes the new champion.
9. Back to **Intake**  with a stronger model—spinning faster with each filing and synthetic adversary.

The fly‑wheel autonomously **discovers goals, invents schemas, extracts, evaluates, and self‑improves**—hardening itself via synthetic edge cases and memory‑augmented critique.

> **North‑Star Outcome**: When any filing is fed into EdgarAI, it returns a perfect JSON/Parquet dataset plus a clickable lineage map—backed by a fly‑wheel that gets better every day with zero human tuning.

---

## 1. Core Principles

| #      | Principle                                  | Impact                                                                                                                        |
| ------ | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| **P1** | **Objective‑First Autonomy**               | The agent chooses *what* to extract before it decides *how*, based purely on corpus patterns and its own observed objectives. |
| **P2** | **Full‑Stack Learning**                    | Prompts, schemas **and model weights** evolve from feedback (LoRA adapters fine‑tuned via RLHF).                              |
| **P3** | **Synthetic Edge‑Case Generation**         | A "Breaker" agent fabricates adversarial clauses so the system hardens itself before real docs change.                        |
| **P4** | **Hierarchical Memory & Ontology**         | Vector memories roll up into a global knowledge graph that unifies concepts across domains.                                   |
| **P5** | **Self‑Budgeting Compute**                 | A meta‑controller decides model size per doc; cost is not a constraint but *risk awareness* is.                               |
| **P6** | **End‑to‑End Provenance & Explainability** | Every cell can be traced back to the exact HTML span, model SHA, prompt hash, critic score, and ontology node.                |

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

| Layer                   | Stored Items                                                                                                                                                                 | Update Cadence | Technology (initial)  |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | --------------------- |
| **Raw HTML Lake**       | Exact filing HTML                                                                                                                                                            | Streaming      | Object store (S3/GCS) |
| **Vector Memory (L0)**  | Embeddings of *all* field‑values, critic notes, breaker samples                                                                                                              | Streaming      | pgvector / FAISS      |
| **Memory Digest (L1)**  | Nightly LLM summaries of L0 shards                                                                                                                                           | Nightly        | DocDB (Elastic)       |
| **Ontology Graph (L2)** | Nodes = canonical concepts; edges = same‑as / broader‑than / causal                                                                                                          | On promotion   | Neo4j                 |
| **Schema Registry**     | Immutable JSON schemas with **LLM‑generated names & alias pointers** (`champion`, `latest`, objective slugs); signed release docs; deprecated branches archived yet callable | On promotion   | Git repo              |
| **Provenance Ledger**   | Row‑level links: (doc id, span, model SHA, prompt SHA, critic score, ontology node)                                                                                          | Streaming      | Append‑only DB        |

---

## 4. LLM Personas (System Prompts)

| Role                     | Purpose                                                         | Key Prompt Directives                                                           |
| ------------------------ | --------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Goal‑Setter**          | Invent or refine extraction objectives from filings + user logs | "Propose the *single most valuable analytical goal* for these docs…"            |
| **Field‑Discoverer**     | List atomic facts in a passage                                  | "Return an array of {candidate\_field, snippet}."                               |
| **Schema‑Synthesizer**   | Cluster candidates → canonical JSON schema                      | "Group synonyms, assign types, minimise field count while maximising coverage." |
| **Prompt‑Writer**        | Turn schema → extraction template                               | "Produce a deterministic JSON spec."                                            |
| **Extractor**            | Pull data from full HTML using template                         | "Fill every field; output one JSON row per logical entity."                     |
| **Critic (with Memory)** | Score rows, citing prior errors                                 | "Grade 0–1; retrieve past failures with similar wording; comment succinctly."   |
| **Tutor / RLHF**         | Revise schema & prompt or fine‑tune weights                     | "Using critic notes, output improved schema & prompt OR LoRA diff."             |
| **Breaker**              | Generate adversarial HTML that fools current extractor          | "Craft plausible credit clauses that exploit extraction weaknesses…"            |
| **Explainer**            | Answer any user question, referencing ontology & provenance     | "Respond conversationally; surface lineage, accuracy stats, caveats."           |

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

## 7. Ontology Alignment Across Objectives

1. After each promotion, embed new field names + definitions.
2. Pairwise cosine > τ ➜ candidate match.
3. LLM confirm‑prompt: "Are ‘Interest Margin’ and ‘Penalty Rate’ semantically equivalent?"
4. If yes, create **same‑as** edge; else new node.
5. Explainer uses graph to answer cross‑domain queries (“show all `CoreRate` fields regardless of schema”).

---

## 8. External Interfaces *(Optional – core loop runs headless)*

### 8.1 Chat API

```http
POST /chat
{ "schema_version": "latest", "messages": [ … ] }
```

* Explainer references ontology + provenance to justify answers.

### 8.2 Batch Extraction API

```http
POST /extract
{ "filing_urls": [ … ], "objective": "auto" }
```

Returns zipped Parquet + provenance ledger.

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
| LoRA fine‑tune          | PEFT + bitsandbytes 4‑bit            |
| RL loop                 | trlX PPO / DPO                       |
| Streaming orchestration | Ray Serve (async DAG)                |
| Vector DB               | pgvector (Postgres 16)               |
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

* **Multimodal Inputs**: add scanned PDF via vision encoder.
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

