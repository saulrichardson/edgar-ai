Ticket: INT-01 – Orchestrator & choose_schema Wiring

Summary
-------
Capture `goal` once and pass it to downstream variant flow.

Tasks
-----
1. In **orchestrator.run_once** move `goal = goal_setter.run(documents)` *before*
   any mention of `discoverer` or `schema_synth`.

2. Pass `goal` into `schema_variants.generate_variants` via its public API (done
   in SCH-02).

3. Temporary backward-compat shim:
   ```python
   try:
       candidates = discoverer.run(docs, goal)
   except TypeError:
       candidates = discoverer.run(docs)
   ```
   Remove this during cleanup phase.

4. Ensure env-flag driven behaviours (`EDGAR_AI_SIMULATE`, `EDGAR_AI_VERBOSE`)
   remain unchanged.

Acceptance Criteria
-------------------
* Entire CLI pipeline (`python -m edgar_ai.cli extract ...`) succeeds both in
  simulate and live modes.
