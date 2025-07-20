Ticket: SCH-02 – Update schema_variants glue layer

Summary
-------
Replace bespoke variant-generation logic with calls to the new goal-aware
Discoverer and Schema-Synth services.

Steps
-----
1. **Delete** existing helpers `generate_variants()` and `merge_referee()` if
   they contain any hard-coded variant logic.

2. Re-implement `generate_variants(doc: Document, minimal_only=False)` as:
   ```python
   goal = goal_setter.run([doc])          # already imported upstream
   candidates = discoverer.run([doc], goal)
   variants   = schema_synth.run(candidates, goal, variants=3)
   return variants
   ```

3. Keep the public API unchanged so `choose_schema.py` continues to import
   `schema_variants.generate_variants`.

4. Ensure simulate mode remains deterministic: both services already honour
   `EDGAR_AI_SIMULATE=1`.

Acceptance Criteria
-------------------
* `choose_schema.py` still runs end-to-end in simulate mode.
* No reference to old `minimal_only` flag after refactor (unless needed for
  backward compatibility).

Out-of-Scope
------------
* Referee logic itself – remains as is.
