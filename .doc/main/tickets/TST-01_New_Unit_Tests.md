Ticket: TST-01 – Unit tests for new goal-aware services

Tests to implement
------------------
1. **test_field_candidate_defaults**
   * Construct `FieldCandidate(field_name="x")` → assert attrs are `None`.

2. **test_discoverer_simulate**
   * Monkeypatch `os.environ["EDGAR_AI_SIMULATE"] = "1"`.
   * Run `discoverer.run([dummy_doc], dummy_goal)`.
   * Assert len(result) >=3 and `result[0].description is not None`.

3. **test_schema_synth_variants_simulate**
   * Run with 5 variants; assert len == 5.
   * All Schema names are unique.

4. **test_memory_goal_hash**
   * Save schema with hash then retrieve via `find_schema_by_goal_hash`.

Note
----
Use fixtures under `tests/fixtures` for dummy HTML.
