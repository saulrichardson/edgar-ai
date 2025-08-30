Ticket: SCH-01 – Goal-Aware Multi-Variant Schema-Synth

Summary
-------
Generate *k* alternative JSON Schemas using function-calling, guided by the
Goal-Setter output and enriched `FieldCandidate`s.

Requirements
------------
1. **Signature**
   ```python
   def run(candidates: list[FieldCandidate], goal: dict, *, variants: int = 3) -> list[Schema]:
   ```

2. **Prompt**
   * System message: instruct LLM to design a *single* schema given goal & field list.
   * User message: JSON payload
     ```json
     {
       "goal": { ... },
       "fields": [ {"name":..., "description":..., "example":...}, ... ]
     }
     ```

3. **Loop Variants**
   * For `i in range(variants)` call the LLM with temperature curve
     `np.linspace(0.2, 0.8, variants)`.
   * Collect the `schema` object returned by the `submit_schema` tool.

4. **Function-Calling Tool**
   ```python
   {
     "name": "submit_schema",
     "parameters": {
       "type": "object",
       "properties": {
         "schema": {
           "$ref": "https://json-schema.org/draft/2020-12/schema"
         }
       },
       "required": ["schema"]
     }
   }
   ```

5. **Return Value**
   * List of `Schema` objects (length == `variants`).

6. **Fallback (simulate mode)**
   * Return `variants` copies of a simple `Schema` with all names typed as `string`.

Acceptance Criteria
-------------------
* `pytest -q` green in simulate mode.
* Manual run against 3 real filings produces 3 distinct schema JSONs.
* Each `Schema.name` is sha256 hash prefix (as existing helper does).

Hints
-----
* Re-use `_SYSTEM_PROMPT` from previous version, append explicit instruction to “respond via function call submit_schema(schema=...)”.
* Post-process required list: if missing → infer `required` for any candidate with `confidence >= 0.8`.

Out-of-Scope
------------
* Schema merging / referee (handled elsewhere).
