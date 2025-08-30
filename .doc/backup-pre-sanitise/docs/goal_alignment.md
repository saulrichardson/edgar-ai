# Goal Alignment & De-Duplication

When `Goal-Setter` produces a new objective JSON, the orchestration layer needs
to decide whether this objective is **brand-new** or effectively the **same as
an existing goal**.  This document describes how that decision is made and
where it is stored.

---

## 1. `goals` table (Postgres)

| column        | type            | notes                                         |
|---------------|-----------------|-----------------------------------------------|
| `goal_id`     | `uuid` PK       | Stable identifier used by downstream tables   |
| `goal_json`   | `jsonb`         | The rich JSON returned by Goal-Setter         |
| `embedding`   | `vector`*       | Embedding of `goal_json["overview"]`          |
| `created_ts`  | `timestamptz`   |                                               |

*`vector` assumes pgvector extension; fallback is `double precision[]`.*

---

## 2. Alignment algorithm (at run-time)

1. Goal-Setter returns `G_new`.
2. Compute embedding `e_new = encoder(G_new["overview"])`.
3. SQL query:

```sql
SELECT goal_id, embedding <=> :e_new AS dist
FROM   goals
ORDER  BY dist ASC
LIMIT  1;
```

4. If `dist ≤ 0.1` (cosine ≥ 0.9), **reuse** `goal_id`.
5. Else create new `goal_id`, insert row.

Python helper (pseudo-code):

```python
match = db.closest_goal(e_new)
if match and match.dist <= 0.1:
    goal_id = match.goal_id
else:
    goal_id = uuid4()
    db.insert_goal(goal_id, G_new, e_new)
```

---

## 3. Down-stream impact

* `schemas`, `prompts`, `rows`, `critic_notes` all reference `goal_id`.  If we
  align to an existing goal, new exhibits join that goal’s learning track and
  benefit from its mature schema.
* If we branch (new goal), Schema-Synth starts from scratch and the fly-wheel
  creates a fresh prompt lineage.

---

## 4. Why no manual taxonomy?

* **Scalability** – The EDGAR corpus grows; new contract sub-types appear all
  the time.
* **Avoids false grouping** – Two exhibits labelled EX-10 may have totally
  different extraction needs.
* **Autonomy** – The LLM is trusted to recognise semantic similarity better
  than heuristic string matching.

---

## 5. Optional human override

* A UI can show “new goal candidates” (those with embedding distance in
  `[0.1 – 0.15]`) for analyst review.
* Analysts can force-merge or force-split goals when domain knowledge beats
  embedding-space proximity.

---

With this alignment layer the system automatically converges similar
objectives and only forks when genuinely new analytical goals emerge.
