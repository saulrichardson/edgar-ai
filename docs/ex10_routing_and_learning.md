# How Edgar-AI Learns to Handle Every Kind of EX-10 Exhibit

> EX-10 covers a zoo of contracts (credit agreements, employment agreements,
> asset-purchase agreements …).  This note explains **how the pipeline discovers
> those sub-types on its own, routes them to specialised schemas, and keeps
> improving without manual routers or hard-coded if/else.**

---

## 1. Goal-Setter is the Router

There is **no hand-written classifier**.  Instead, `Goal-Setter` reads the
exhibit text and asks the LLM:

```text
"Given this text, what is the most valuable extraction objective?"
```

The answer *is* the routing decision:

| Exhibit contains …                           | LLM goal string                                    |
|----------------------------------------------|-----------------------------------------------------|
| "Revolving Credit Facility…"                 | Extract borrower, lender, loan amount…             |
| "Employment Agreement between …"            | Extract employee name, title, base salary…         |
| "Asset Purchase Agreement dated …"          | Extract buyer, seller, purchase price, closing…    |

The goal is stored as `goal_id` (hash of the text) and feeds every downstream
persona.

---

## 2. Separate Learning Tracks per `goal_id`

```
doc  ─▶ goal_setter ─▶ goal_id_X
                     │
                     ├─▶ discoverer + schema_synth → schema_vX.1
                     ├─▶ prompt_builder / extractor
                     └─▶ critic → tutor → governor
```

Each goal maintains **its own** schema, prompt history and score trajectory.
Credit-agreement goals never pollute employment-agreement schemas.

---

## 3. Promoting New Concepts (fork)

1. All raw field candidates land in `field_candidates`.
2. Nightly SQL aggregates support counts → `concept_backlog`.
3. When a field appears in ≥ *promotion_threshold* distinct docs, Schema-Synth
   promotes it, creating *schema_v+1* for the same `goal_id` **or** a *new*
   `goal_id` if the critic shows systemic divergence.

Example:

```
credit_agreement goal  (v1)  fields = [borrower, lender, loan_amount, interest_rate]
                              ↓
backlog finds "prepayment_penalty" appeared in 15 docs
                              ↓
schema_v2 = v1 + prepayment_penalty
```

---

## 4. Merging Goals (convergence)

If two goals reach ≥95 % average critic score **and** their field sets overlap
≥90 %, Governor can deprecate one goal and re-tag its rows to the other.  This
keeps the taxonomy from exploding.

---

## 5. Back-fill for Historical Consistency

When a schema gains new fields, a background worker re-extracts affected
filings, writing `row_version=2` rows so analytics always see the latest
columns.

---

## 6. Human Oversight (optional but minimal)

* **Review queue** – newly promoted goals/schemas can wait for human approval.
* **Issue Critic** – analysts can file errors; Critic treats them as
  high-severity until resolved.

Everything else—routing, schema growth, merging, and back-fill—happens without
manual code or rule changes.

---

With this mechanism Edgar-AI can ingest every flavour of EX-10 (and any other
exhibit) while autonomously refining its understanding as more filings arrive.
