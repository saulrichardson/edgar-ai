Ticket: DISC-02 – Goal-Aware Discoverer v2

Summary
-------
Refactor Discoverer persona so it leverages the **Goal-Setter output** and
returns enriched `FieldCandidate`s using OpenAI function-calling.  Maintain
offline simulation path.

Detailed Requirements
---------------------
1. **Signature Change**
   ```python
   def run(documents: list[Document], goal: dict) -> list[FieldCandidate]:
   ```

2. **Prompt Construction**
   * System message: describe task and exact JSON schema for `FieldCandidate`.
   * User #1 message: `json.dumps(goal)` – serves as information-theoretic
     context.
   * User #2 message: full exhibit text (no truncation).

3. **Function-Calling**
   * Define `FIELD_CANDIDATE_JSON_SCHEMA` once in the module.
   * Create a tool schema `submit_fields` with a single property `fields`.
   * Pass `tools=[...]`, `tool_choice={"name":"submit_fields"}` to
     `chat_completions()`.

4. **Response Parsing**
   * Extract the first tool_call → `arguments` → `fields` → map to
     `FieldCandidate` objects.
   * Any parse failure raises `RuntimeError` (pipeline will retry at
     choose_schema level).

5. **Simulation Mode** (`EDGAR_AI_SIMULATE=1`)
   * Return three static `FieldCandidate`s:
     ```python
     [
       FieldCandidate(field_name="company_name", description="Stub", confidence=1.0),
       FieldCandidate(...)
     ]
     ```

6. **Logging**
   * Respect env `EDGAR_AI_VERBOSE`; log raw LLM content at DEBUG.

7. **Backwards Compatibility**
   * Add temporary wrapper:
     ```python
     def run(documents, goal=None):
         if goal is None:
             # fallback to legacy behaviour until INT-01 removed
     ```

Acceptance Criteria
-------------------
* Unit test in simulate mode returns objects with non-None description & confidence.
* Live gateway returns valid JSON for at least 5 filings (manual QA).
* No hardcoded length truncation remains.

Implementation Hints
--------------------
* Keep temperature configurable via `settings.discoverer_temperature`.
* Guardrail: if LLM returns >50 fields, log warning and slice to 50.

Out-of-Scope
------------
* Self-consistency voting (will be tackled later).
