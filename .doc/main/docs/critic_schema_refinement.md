# ⚠️ *Archived note* – The strategy below predates the unified Critic ↔ Tutor
# feedback loop and is kept only for historical reference.
#
# Automatic Detection of Schema Over- and Under-Compression

Status: concept – Critic/Tutor/Governor loop not yet implemented

The first-pass Variant → Referee flow produces a **reasonable** initial schema
but cannot guarantee the optimal granularity.  Sometimes the LLM collapses too
many concepts into a single umbrella field (*over-compression*).  Other times
it flattens obviously repeating structures into dozens of sparse fields
(*under-compression*).

The long-term fix belongs to the *learning* phase of the pipeline rather than
to hard-coded prompt tweaks.  This note captures the intended logic so future
contributors can wire it in without guessing.

---

## 1  Critic — metrics & heuristics

After extraction the Critic has:

* the **schema** used for this run;
* the **exhibit text**;
* the **row(s)** returned by the extractor.

The Critic computes lightweight metrics:

| Signal                         | What it indicates                      |
|--------------------------------|----------------------------------------|
| **Field-entropy** (Shannon)    | Very low ⇒ too few distinct fields     |
| **Non-null ratio** per field   | Many ≥90 % null ⇒ under-compression    |
| **Prefix redundancy**          | term_a_, term_b_, … ⇒ under-compression|
| **Blob length** (> X chars)    | One field encodes many facts ⇒ over    |

It then emits structured `CriticNote`s, e.g.

```json
{
  "message": "Over-compression: only 2 fields extracted but at least 12 distinct concepts detected in text.",
  "severity": "warning",
  "code": "OVER_COMPRESSION"
}
```

---

## 2  Tutor — challenger schema synthesis

Tutor receives the CriticNotes and the original schema.  High-level logic:

* OVER_COMPRESSION ⇒ **split** composite fields based on concept detection
  (LLM can read the text and propose a set of new field candidates).
* UNDER_COMPRESSION ⇒ **group** repetitive prefixes into nested arrays or
  objects.

Tutor outputs a **challenger schema**.

---

## 3  Governor — A/B evaluation

Governor runs both **champion** (current) and **challenger** schemas on a
battery of recent exhibits and compares:

* Critic average score (must improve by Δ ≥ 0.05).
* Token cost increase must stay below a configurable budget.

If challenger wins, Governor promotes it and marks the old schema as
`deprecated` in the registry.

---

## 4  Back-fill & lineage

When a new champion replaces an over- or under-compressed predecessor,
historical filings are **re-extracted** so the ledger stays consistent.

Lineage tables store

* `parent_schema_id`  – which schema was superseded;
* `note`              – promotion rationale from Governor.

---

## 5  Implementation roadmap

1. **Hook**: Critic metrics in `services/critic.py` (currently stub).
2. **Responder**: Tutor rewrite prompt that applies the heuristics.
3. **Evaluator**: Governor A/B logic + simple scoring threshold.
4. **Migration**: add promotion lineage columns to `schemas` table.
5. **Back-fill worker**: re-run extraction for older filings.

With this loop in place prompt tweaks become merely *hints*; the system will
autonomously converge on the right level of granularity over time.
