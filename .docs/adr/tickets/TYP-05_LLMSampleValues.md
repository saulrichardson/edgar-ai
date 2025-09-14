# TYP-05 — Transient LLM “Sample-Value” Helper (Backlog)

**Status:** Ideation  
**Owner:** TBD  
**Target Release:** Post-MVP, once the extraction path has stabilised

## Context

During schema design we occasionally mis-classify JSON primitive types
(e.g. treating monetary amounts as strings).  A proposed fix was to ask the
LLM to quote one *verbatim* example value for every field so that
`Schema-Synth` can infer the correct type.  The sample would be used **only
in-memory** and would *not* be stored in the persisted schema.

## Why it is not implemented now

1. Adds token cost + complexity while the Discoverer regex module still
   exists.
2. Requires an additional function parameter or prompt change that would
   churn integration tests during the current refactor cycle.
3. The team has prioritised wiring the Min/Mid/Max schema-variant flow and
   restoring field-level rationale—both higher impact on extraction quality.

## Idea (to revisit)

1. Extend `schema_synth` system prompt:

   ```text
   For each field ALSO return an `x-sample_value` key containing one
   verbatim example from the exhibit if present.
   ```

2. In the parsing loop, read `x-sample_value` and use it *only* for:
   * primitive-type inference (number vs string)
   * optional pattern derivation (currency, percentage, ISO-date)
   The key is discarded afterwards.

3. Keep the public `Schema` object unchanged so downstream services are not
   impacted.

## Acceptance criteria

* End-to-end pipeline shows ≥ 90 % correct primitive typing on the
  validation corpus **without** hand-coded regex rules.
* No exhibit-specific literals are persisted to the schema registry or row
  storage.

---

> NOTE: This ticket only memorialises the concept; no code in the current
> repository should attempt to collect `x-sample_value`.  Implement in a
> dedicated feature branch when prioritised.

