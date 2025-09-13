Ticket: MEM-01 – Goal-Hash based Schema Lookup

Problem
-------
Schemas are currently retrieved by sequential ID only. We want to reuse
schemas that satisfy the *same information-theoretic goal* instead of
duplicating work.

Deliverables
------------
1. Extend **SchemaRecord**
   * Add `goal_hash: str | None` (12-char SHA256 prefix).

2. **FileMemoryStore**
   * When saving a new schema record via `save_schema_record`, accept optional
     `goal_hash` param and persist it alongside the schema JSON.
   * Implement `find_schema_by_goal_hash(goal_hash: str)`.

3. **Backfill** – existing JSON file may lack the column.  Loader must default
   to `None` if key absent.

4. **Helper** in utilities
   ```python
   def hash_goal(goal: dict) -> str:
       return hashlib.sha256(json.dumps(goal, sort_keys=True).encode()).hexdigest()[:12]
   ```

5. Unit tests:
   * Save schema with hash then retrieve.
   * Load old-style record (without hash) → still works.

Acceptance Criteria
-------------------
* `choose_schema` short-circuits variant generation if a matching hash is
  found.
* No migration errors when reading existing store.
