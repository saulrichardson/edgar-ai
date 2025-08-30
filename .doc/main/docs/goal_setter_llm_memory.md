# LLM-Driven Schema Memory (No Embeddings)

This document outlines how to orchestrate schema reuse and creation purely via LLM-driven reasoning—without any document-type keys or embeddings-based similarity.

## 1. Store Multiple Schema Records with Rationales

Each time you generate a new schema, persist it in memory along with a brief rationale (e.g. the exhibit text or chain-of-thought summary).  Memory should accumulate all prior schemas:

```python
class SchemaRecord(BaseModel):
    schema_id: str
    schema: dict       # the overview/topics/fields JSON
    rationale: str     # short description or summary of why this schema applies

class MemoryStore(ABC):
    def save_schema_record(self, schema_id: str, schema: dict, rationale: str) -> None:
        ...

    def list_schema_records(self) -> List[SchemaRecord]:
        ...
```

Provide an in-memory implementation first; later you can swap in a persistent store.

## 2. Retrieve Candidate Schemas

When processing a new exhibit, load all stored schemas for the LLM to consider:

```python
records = memory.list_schema_records()
```

## 3. Use the LLM to Select (or Create) the Best Schema

Prompt the LLM with the existing schemas and the new exhibit.  Ask it to pick the best-fit schema by number, or to produce a brand-new schema if none applies.

```text
SYSTEM:
You have these previously generated extraction schemas (overview/topics/fields):
1) { ...schema A... }
2) { ...schema B... }
3) { ...schema C... }

Given the exhibit text below, return ONLY valid JSON with two keys:
- "choice": the number (1/2/3) of the best-fit schema, or 0 if none fits.
- "new_schema": if "choice" is 0, include a full schema object with keys overview, topics, and fields; otherwise null.

EXHIBIT:
"""
<insert exhibit text here>
"""

Example valid responses:
```json
{ "choice": 2, "new_schema": null }
```
```json
{
  "choice": 0,
  "new_schema": {
    "overview": "...",
    "topics": ["..."],
    "fields": ["..."]
  }
}
```
```

If the LLM returns choice 0, invoke the Goal-Setter to generate a new schema and save it via `save_schema_record`.

## 4. Pipeline Orchestration Sketch

Combine the LLM-driven selection step with schema creation and downstream extraction:

```python
# Prompt template for choosing or creating a schema
CHOICE_PROMPT = """You have these previously generated extraction schemas (overview/topics/fields):
{schemas}

Given the exhibit text below, return ONLY valid JSON with two keys:
- "choice": the number (1/2/3/...) of the best-fit schema, or 0 if none fits.
- "new_schema": if "choice" is 0, include a full schema object with keys overview, topics, and fields; otherwise null.

EXHIBIT:
"""{exhibit}"""
"""

def choose_schema(doc: Document, memory: MemoryStore) -> dict:
    records = memory.list_schema_records()
    # ask the LLM to pick among existing schemas or propose a new one
    decision = llm_gateway.chat_completions(
        model=settings.model_goal_setter,
        messages=[
            {"role": "system", "content": CHOICE_PROMPT.format(
                schemas=[r.schema for r in records],
                exhibit=doc.text,
            )},
        ],
        temperature=settings.goal_setter_temperature,
    )
    payload = json.loads(decision)

    # reuse existing schema if indicated
    choice = payload.get("choice", 0)
    if 1 <= choice <= len(records):
        return records[choice - 1].schema

    # otherwise generate and save a new schema
    new_schema = goal_setter.run([doc])
    schema_id = f"schema_{len(records) + 1}"
    memory.save_schema_record(schema_id, new_schema, rationale=doc.text)
    return new_schema

def run_pipeline(doc: Document, memory: MemoryStore) -> Any:
    schema = choose_schema(doc, memory)
    # TODO: extract rows per schema (pass whole document to the API) and assemble final table
    return schema

## 5. Cold Start vs. Subsequent Runs

This flow handles both the initial “cold start” (no schemas in memory yet) and later “warm start” cases:

1. **Cold Start**  
   - `memory.list_schema_records()` returns an empty list.  
   - `choose_schema()` invokes the LLM, which replies with `"choice": 0` and a `new_schema`.  
   - A new schema is created via `goal_setter.run()`, saved in memory, and immediately used for extraction.

2. **Warm Start**  
   - `memory.list_schema_records()` returns one or more prior schemas.  
   - `choose_schema()` invokes the LLM, which selects the best-fit schema by number.  
   - The chosen schema is reused directly for extraction without re-generating it.

This ensures that after the first generation, subsequent documents automatically follow the main route of reusing stored schemas and extraction logic.
```

This LLM-driven flow ensures that schema reuse and creation are guided by language reasoning alone—no metadata or embeddings required.