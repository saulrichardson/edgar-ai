# Exhibit Type vs. Learned Goal – Why We Don’t Hard-Code Routing

EDGAR labels every attachment with a formal *exhibit type* (e.g., **EX-10.1**),
but Edgar-AI’s fly-wheel **does not** rely on that label to choose how it
extracts data.  Here’s why, and how the two concepts coexist without data
leakage.

| Concept            | Source               | Used for…                    | Learning impact |
|--------------------|----------------------|------------------------------|-----------------|
| `exhibit_type`     | Up-stream EDGAR parser| UI filters, audit, metadata  | *None*          |
| `goal_id`          | LLM Goal-Setter      | Schema, prompt, critic loops | **Everything**  |

## 1  LLM decides the route

* **Goal-Setter** reads the exhibit *text only* (no type hint) and returns a
  rich JSON objective.  The SHA-256 hash of that JSON becomes `goal_id`.
* Every learning artefact—schemas, prompts, rows, critic notes—is keyed by
  `goal_id`.
* If two EX-10 exhibits share the same learned objective, they share the same
  `goal_id`; if they differ, they fork.

## 2  Why we avoid exhibit_type in the prompt

1. **Data-Leakage Risk**  Exhibit labels may indirectly encode the answer
   (e.g., "Credit Agreement" text in the type string).
2. **Robustness**  Up-stream parsers sometimes mis-label attachments; the LLM
   can still infer purpose from the content.
3. **Generalisation**  International filings or PDFs may have no EDGAR-style
   exhibit code—content inference still works.

## 3  Tables keyed by goal_id, not exhibit_type

| Table               | Key column(s)          |
|---------------------|------------------------|
| `schemas`           | `schema_hash`, `goal_id`|
| `prompts`           | `prompt_hash`, `goal_id`|
| `rows`              | `row_id`, `goal_id`    |
| `critic_notes`      | `row_id`, `goal_id`    |

`exhibit_type` is kept as a *non-index* metadata column for audit and
dashboard filtering only.

## 4  Optional future hinting

If we ever decide to bias the LLM with the EDGAR code, we can append a single
line to the Goal-Setter system prompt:

```python
hint = doc.metadata.get("exhibit_type")
if hint:
    system_prompt += f"\n\nExhibit type hint: {hint}"
```

Because all routing still depends on the resulting `goal_id`, human error in
type labels would be *mitigated* rather than amplified.

---
In short, **`goal_id` is the autonomous routing key**, while
`exhibit_type` stays a helpful but non-critical piece of metadata.
