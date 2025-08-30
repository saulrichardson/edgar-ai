Ticket: DISC-01 – Extend FieldCandidate dataclass

Summary
-------
Add richer metadata to `interfaces.FieldCandidate` so downstream services can
reason with more context than just the field *name*.

Background / Rationale
----------------------
The current model only carries `field_name`.  Upcoming goal-aware discovery
and schema synthesis steps will benefit from:

* `description` – short human explanation for Prompt-Builder & Docs.
* `example`     – sample raw value used for type inference and UX.
* `confidence`  – float 0-1 so we can soft-rank candidates.

Scope of Work
-------------
1. **src/edgar_ai/interfaces.py**
   * Update the `FieldCandidate` pydantic model:
     ```python
     class FieldCandidate(BaseModel):
         field_name: str
         description: str | None = None
         example: str | None = None
         confidence: float | None = None
     ```
   * All additional attributes must be optional with sensible defaults so
     legacy code continues to work.

2. **Simulate Mode Defaults** – wherever `FieldCandidate` is constructed in
   simulate paths (Discoverer, unit tests) provide `description` and
   `confidence=1.0` so no `None` leaks into debug logs.

3. **Unit Test** – add `tests/test_interfaces.py` verifying:
   * Model accepts only `field_name` (backward compat).
   * Accepts full spec with description/example/confidence.

Acceptance Criteria
-------------------
* Typing passes: `mypy` still green.
* `pytest -q` passes with no regression.
* No errors in simulate mode (`EDGAR_AI_SIMULATE=1`).

Implementation Hints
--------------------
* Because `confidence` is optional, downstream ranking code should default to
  `0.5` if the attribute is `None`.

Out-of-Scope
------------
* No changes to database / storage layer yet – that happens in MEM-01.
