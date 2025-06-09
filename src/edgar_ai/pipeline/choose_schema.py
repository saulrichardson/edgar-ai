"""LLM-driven selection or creation of the best-fit extraction schema."""

from __future__ import annotations

import json
from typing import List

from ..clients import llm_gateway
from ..config import settings
from ..interfaces import Document
from ..memory import MemoryStore, SchemaRecord
from ..services import goal_setter


CHOICE_PROMPT = (
    "You have these previously generated extraction schemas (overview/topics/fields):\n"
    "{schemas}\n\n"
    "Given the exhibit text below, return ONLY valid JSON with two keys:\n"
    "- \"choice\": the number (1/2/3/...) of the best-fit schema, or 0 if none fits.\n"
    "- \"new_schema\": if \"choice\" is 0, include a full schema object with keys overview, topics, and fields; otherwise null.\n\n"
    "EXHIBIT:\n"
    "\"\"\"{exhibit}\"\"\"\n"
)


def choose_schema(doc: Document, memory: MemoryStore) -> dict:
    """Select an existing schema or create a new one via the LLM and persist it."""

    records: List[SchemaRecord] = memory.list_schema_records()
    # Ask the LLM to pick among existing schemas or propose a new one
    response = llm_gateway.chat_completions(
        model=settings.model_goal_setter,
        messages=[
            {"role": "system", "content": CHOICE_PROMPT.format(
                schemas=[r.schema for r in records],
                exhibit=doc.text,
            )},
        ],
        temperature=settings.goal_setter_temperature,
    )
    content = response["choices"][0]["message"]["content"]
    payload = json.loads(content)

    # Reuse existing schema if indicated
    choice = payload.get("choice", 0)
    if 1 <= choice <= len(records):
        return records[choice - 1].schema

    # Otherwise generate and save a new schema
    new_schema = goal_setter.run([doc])
    schema_id = f"schema_{len(records) + 1}"
    memory.save_schema_record(schema_id, new_schema, rationale=doc.text)
    return new_schema