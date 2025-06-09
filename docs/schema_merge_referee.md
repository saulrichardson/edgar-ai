# Schema Merge-Referee – future enhancement notes

Status: **IDEA / not yet implemented**

This document captures a design option that came up during discussion of the
variant-selection flow.  Today the pipeline generates 2-3 candidate schemas
(maximalist, minimalist, balanced) and the **Referee** LLM simply *chooses* the
best one.  A richer alternative is to let the Referee **synthesise** a new
schema by merging the strengths of multiple variants.

---

## Why “pick-one” was chosen first

1. **Determinism** – returning `winner_index` is idempotent and easy to audit.
2. **Validation** – every candidate is known to satisfy the JSON contract;
   merging would require a second parse/validate loop.
3. **Latency** – pick-one adds a single LLM call; merge would add another
   payload round-trip with a bigger response body.
4. **Lineage** – easy to trace which stored schema a row came from.

These points made the minimal “choose the winner” approach the safest way to
ship the variant workflow.

---

## When a merge step becomes valuable

* **Complementary strengths** – e.g. variant-A captures *parties* perfectly,
  variant-B encodes a richer *facilities* array.
* **Critic feedback** consistently flags gaps that could be filled by
  combining variants.
* **Schema churn** – new required fields appear in different variants across
  runs, causing oscillation.

---

## Sketch of a Merge-Referee protocol

1. **Input** – Same as today: list of candidate schemas + exhibit text.
2. **System prompt** –

   ```text
   If no candidate fully satisfies the principles, output:
   {
     "winner_index": -1,
     "merged_schema": { …combined schema JSON… },
     "reason": "why merge was necessary"
   }
   Otherwise behave as today and return winner_index ≥ 0.
   ```

3. **choose_schema() changes**
   * If `winner_index >= 0` → keep the current path.
   * If `winner_index == -1` → validate `merged_schema`, persist it, mark its
     lineage (e.g. parent_hash = variant ids).

4. **Governor logic** – when a merged schema is promoted, mark superseded
   variants as inactive to avoid clutter.

---

## Open Questions

* **Validation budget** – Should we re-run Critic immediately on the merged
  schema before promotion?
* **Conflict resolution** – If two fields collide (same name, different
  types), what rule wins?  Could delegate this reasoning to the LLM or apply a
  deterministic tie-break.
* **Prompt size** – Large exhibits + ≥3 schemas + merged response might exceed
  context for smaller models; require 100k-token models or truncation.

---

## Next steps (when needed)

1. Monitor Critic notes for "could combine features of variants" signals.
2. If frequent, prototype the merge protocol behind a feature flag
   `EDGAR_AI_ENABLE_MERGE_REFEREE`.
3. Start with simple union-merge logic (no conflict resolution) and iterate.

Until those needs arise, the existing **pick-one** flow remains the default
because it is simpler, cheaper, and easier to debug.
