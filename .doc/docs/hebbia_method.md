# Replicating Hebbia‑Grade Covenant Extraction for an EDGAR‑Focused Tool

## 0. Executive Summary

This document is a **full, end‑to‑end blueprint** for building a covenant‑extraction pipeline that rivals Hebbia’s performance, while tailoring inputs to U.S. SEC EDGAR filings (10‑K, 10‑Q, 8‑K exhibits, credit agreements, indentures, etc.). It covers:

1. **Functional Requirements** and success metrics
2. **System Architecture** with component‑level design
3. **Ingestion & Pre‑processing** pipelines for EDGAR sources
4. **Covenant Section Identification** models
5. **Field‑Level Extraction & Normalization** agents
6. **Knowledge Graph & Ontology** for downstream analytics
7. **Quality Assurance & Benchmarking**
8. **Security, Compliance, & Deployment**
9. **Integration Hooks** into existing “General EDGAR Extraction” flows
10. **Future Enhancements & Roadmap**

Use this as a living design spec—update or annotate sections as you iterate.

---

## 1. Functional Requirements

| ID    | Requirement                                                                            | Target KPI                    |
| ----- | -------------------------------------------------------------------------------------- | ----------------------------- |
| FR‑1  | Ingest 1,000+ EDGAR filings (≤ 10 GB) in < 2 hrs                                       | ≤ 2 h end‑to‑end              |
| FR‑2  | Detect covenant sections with ≥ 95 % recall, ≥ 90 % precision                          | F‑macro ≥ 0.92                |
| FR‑3  | Extract numerical thresholds (ratios, percentages, \$ limits) with ±1 % relative error | MAPE ≤ 1 %                    |
| FR‑4  | Round‑trip latency for *single‑document* query ≤ 5 s (P95)                             | P95 ≤ 5 s                     |
| FR‑5  | Full lineage (page, line, byte offset) stored for every extracted field                | 100 % coverage                |
| NFR‑1 | SOC 2 Type II controls; opt‑out of model‑training on client data                       | Accepted by Risk & Compliance |

---

## 2. High‑Level Architecture

```
┌──────────────────────────┐      ┌──────────────────────┐
│ 1  Ingestion Orchestrator │──┐  │ 2  Document Store    │
└──────────────────────────┘  │  └──────────────────────┘
             ▼                │                ▲
╔═════════════════════════════╧════════════════╧════════════╗
║ 3  Pre‑processing & OCR (AWS Textract + Tesseract)       ║
╚══════════════════════════════════════════════════════════╝
             ▼
╔══════════════════════════════════════════════════════════╗
║ 4  Section Classifier (Affirmative/Negative/Financial)   ║
║    • fine‑tuned Llama‑3 8B + BM25 hybrid                 ║
╚══════════════════════════════════════════════════════════╝
             ▼
╔══════════════════════════════════════════════════════════╗
║ 5  Extraction Agents (LangGraph DAG)                     ║
║    • regex/NER catchers  • ratio parser  • date parser   ║
║    • leverage multi‑agent fan‑out, chunk‑level context   ║
╚══════════════════════════════════════════════════════════╝
             ▼
╔══════════════════════════════════════════════════════════╗
║ 6  Normalizer & Ontology Mapper (Pydantic models)        ║
╚══════════════════════════════════════════════════════════╝
             ▼
╔══════════════════════════════════════════════════════════╗
║ 7  Vector & Relational Stores                            ║
║    • Qdrant (embeddings)   • Postgres (canonical fields) ║
╚══════════════════════════════════════════════════════════╝
             ▼
╔══════════════════════════════════════════════════════════╗
║ 8  API Layer (FastAPI) & Matrix‑style UI (Next.js)       ║
╚══════════════════════════════════════════════════════════╝
```

---

## 3. Ingestion & Pre‑processing

### 3.1 Source Acquisition

* **Primary**: SEC’s Bulk Download via FTP + RSS feed for daily deltas.
* **File Types**: HTML, TXT, PDF exhibits (`EX‑10.x`).
* **Versioning**: Hash every file; store “CIK‑Accession‑Version” key.

### 3.2 OCR & Text Extraction

| File type   | Toolchain                                      | Notes                                    |
| ----------- | ---------------------------------------------- | ---------------------------------------- |
| Scanned PDF | AWS Textract *or* GCP Document AI (Vision OCR) | Enable table detection & bounding boxes. |
| Native PDF  | `pdfminer‑six` + `pdfplumber`                  | Preserve layout coordinates.             |
| HTML/TXT    | `BeautifulSoup`, stripping inline XBRL         | Convert to UTF‑8.                        |

### 3.3 Chunking Strategy

* **Recursive Text Splitter** at 400 tokens, 20 % overlap.
* Attach metadata: `section_hint`, `page_num`, `bbox`, `file_hash`.

### 3.4 Deduplication & Compression

* **MinHash + SimHash** to find near‑duplicates (common in multiple exhibit re‑filings).
* Store canonical copy; keep pointers to dup IDs for lineage.

---

## 4. Covenant Section Identification

### 4.1 Label Taxonomy

| Label                 | Regex Seed         | Examples         |                                            |                                            |
| --------------------- | ------------------ | ---------------- | ------------------------------------------ | ------------------------------------------ |
| AFFIRMATIVE\_COVENANT | “shall (maintain   | deliver          | preserve)”                                 | "Borrower shall maintain insurance…"       |
| NEGATIVE\_COVENANT    | “shall not (incur  | create           | declare)”                                  | “Company shall not incur additional debt…” |
| FINANCIAL\_COVENANT   | “Maximum (Leverage | Debt to EBITDA)” | “Maximum Total Net Leverage Ratio of 4.0x” |                                            |

### 4.2 Model

* **Hybrid Classifier** = BM25 ranker → re‑rank w/ fine‑tuned `llama‑3‑8b‑instr` (LoRA on 30k labeled covenant spans).
* **Evaluation**: 5‑fold CV, F1≥0.92.

---

## 5. Field‑Level Extraction Agents

### 5.1 Agent Graph

```
Section ➜ [Text‑Puller] ➜ [Entity‑Collector] ➜ [Value‑Parser]
                               │                    │
                               └──► [Unit‑Normalizer] ─► [Validator]
```

* **Text‑Puller**: returns raw sentence windows ±2 sentences around regex hits.
* **Entity‑Collector**: spaCy + custom rules capture metric names, thresholds, comparators.
* **Value‑Parser**: converts “greater of (i) \$50,000,000 and (ii) 35 % of EBITDA” into structured AST.
* **Unit‑Normalizer**: standardises bps, %, x‑turns.
* **Validator**: cross‑checks parser output; flags anomalies to human.

### 5.2 Parallelisation

* Use **LangGraph** DAG with fan‑out across covenant types; each chunk processed in parallel→ reduces wall time.

---

## 6. Normalization & Ontology

### 6.1 Pydantic Schema

```python
class FinancialCovenant(BaseModel):
    agreement_id: str
    covenant_type: Literal["Leverage", "InterestCoverage", "FixedCharge"]
    threshold: Decimal
    comparator: Literal["<=", ">=", "<", ">"]
    test_frequency: Literal["Quarterly", "Semi‑Annual", "Annual"]
    citation: CitationMeta
```

### 6.2 Knowledge Graph

* **Nodes**: Agreement, Borrower, Lender, Covenant, Threshold.
* **Edges**: `HAS_COVENANT`, `TESTED_AT`, `LINKED_TO_ENTITY`.

---

## 7. Quality Assurance & Benchmarking

| Stage             | Metric                    | Tooling                                   |
| ----------------- | ------------------------- | ----------------------------------------- |
| Section detection | Precision/Recall          | `scikit‑learn`, manual spots via Prodigy. |
| Field extraction  | Exact Match %, MAPE       | Great Expectations tests.                 |
| End‑to‑end        | Analyst review time saved | Time‑on‑task logging.                     |

*Maintain a **gold corpus** of 200 manually tagged agreements; re‑run nightly CI.*

---

## 8. Security, Compliance, & Deployment

* **Data Residency**: S3 buckets in `us‑east‑1`; encryption at rest (SSE‑KMS).
* **Transit**: TLS 1.3 everywhere; VPC endpoints for Textract & Qdrant.
* **Access Control**: OAuth2 + row‑level Postgres RLS; audit trail via AWS CloudTrail.
* **Model Privacy**: Set `data_usage_opt_out=true` on OpenAI calls; purge logs after 30 days.
* **Deployment**: Docker compose → ECS Fargate; autoscale workers & agents.

---

## 9. Integration with General EDGAR Extraction Tool

1. **Shared Downloader** – reuse your existing EDGAR fetcher; push exhibit PDFs into Ingestion SQS.
2. **Modular Section** – expose covenant extractor as `/v1/covenants/extract` endpoint callable by your current pipeline.
3. **Unified Index** – merge covenant output into your existing Postgres schema; add `covenant_*` columns.
4. **UI Embed** – iframe the new Matrix grid in your tool’s Deal dashboard.

---

## 10. Future Enhancements

| Idea                                           | Impact        | ETA     |
| ---------------------------------------------- | ------------- | ------- |
| 10K inline XBRL cross‑linking (debt footnotes) | +3 % recall   | Q4 2025 |
| Fine‑tune `gpt‑5o‑mini` on covenant span QA    | –15 % latency | Q1 2026 |
| Automated redlining vs prior amendments        | New feature   | Q2 2026 |

---

## 11. Reference Stack

* **OCR**: AWS Textract, GCP Document AI
* **Embeddings**: `text‑embedding‑3‑large`
* **Vector DB**: Qdrant v1.9
* **LLM**: OpenAI `gpt‑4o‑mini` (reasoning), Llama‑3‑8b‑LoRA (classification)
* **Agents**: LangGraph‐0.5, Flyte for orchestration
* **DevOps**: Docker, ECS, Terraform, GitHub Actions CI/CD

---

### Authors & Revision History

| Date       | Author              | Notes         |
| ---------- | ------------------- | ------------- |
| 2025‑07‑07 | OpenAI o3 (ChatGPT) | Initial draft |

