# Optional "Merge-then-Referee" Flow – Pros, Cons, and a Hybrid Approach

The extraction pipeline currently follows this **3-step** pattern:

1. **Variant generation** – The LLM produces three schemas (maximalist, minimalist, balanced).
2. **Referee** – A judging LLM selects the "best" of the three.
3. **Extraction** – The chosen schema drives the extractor prompt.

## Proposal that surfaced

> “Let the referee LLM *merge* the three variants into a *new* schema, then choose between the four (original 3 + merge).”

## Downsides of a Blind Merge

| # | Issue | Impact |
|---|-------|--------|
|1 | **Un-anchored creativity** | Merge model may invent fields absent from exhibit & variants, re-introducing hallucination risk. |
|2 | **Loss of provenance** | Harder to trace which prompt produced each field; audit/debug complexity. |
|3 | **Schema drift** | Extra stochastic step ⇒ different schema text on identical inputs, creating version-churn for downstream DB/ETL. |
|4 | **Latency & cost** | +1 LLM call (~25-30 % more tokens + wall time). |
|5 | **Double judgement paradox** | If referee ultimately discards the merge, merge cost is pure waste; if it always keeps the merge, initial referee step is redundant. |
|6 | **Validation overhead** | Need to re-run sanity checks on merged output; more branches, more failure modes. |
|7 | **Human cognitive load** | Logs/telemetry now show four candidates; manual diffing/historical comparison harder. |

## When a Merge *Can* Help

* None of the three variants individually meets quality thresholds.  Examples:
  * Maximalist too noisy.
  * Minimalist misses critical datapoints.
  * Balanced has confusing field names.

## Suggested Hybrid Strategy – *Merge Only When Needed*

1. **Run referee on the three variants** as we do today.
2. **Check quality signal** – e.g., referee returns a low confidence score or an explicit flag "no winner".
3. **If and only if** winner is unsatisfactory → call a *merge LLM* to synthesise a schema **and accept it directly** (skip a second referee cycle).

This keeps the common path fast and stable while preserving a safety valve for edge cases.

---

*Document created 2025-06-09 to memorialise discussion on future pipeline directions.*