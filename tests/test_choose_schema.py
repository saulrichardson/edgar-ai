"""Unit tests for the choose_schema pipeline step (cold vs. warm start)."""

import sys
from pathlib import Path

# Ensure src/ is on PYTHONPATH for test imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

import json
import pytest

from edgar_ai.interfaces import Document
from edgar_ai.memory import InMemoryStore
from edgar_ai.pipeline.choose_schema import choose_schema
from edgar_ai.clients import llm_gateway


def test_choose_schema_cold_start(monkeypatch):
    memory = InMemoryStore()
    doc = Document(doc_id="doc1", text="dummy text")

    # Stub LLM to return choice 0 with a new schema
    new_schema = {"overview": "ov", "topics": ["t"], "fields": ["f1"]}
    response_content = json.dumps({"choice": 0, "new_schema": new_schema})
    monkeypatch.setattr(
        llm_gateway,
        "chat_completions",
        lambda **kwargs: {"choices": [{"message": {"content": response_content}}]},
    )

    # Stub goal_setter to return the new schema
    import edgar_ai.services.goal_setter as gs_mod

    monkeypatch.setattr(gs_mod, "run", lambda docs: new_schema)

    schema = choose_schema(doc, memory)
    assert schema == new_schema

    records = memory.list_schema_records()
    assert len(records) == 1
    record = records[0]
    assert record.schema_id == "schema_1"
    assert record.schema == new_schema
    assert record.rationale == doc.text


def test_choose_schema_warm_start(monkeypatch):
    memory = InMemoryStore()
    first = {"fields": ["a"]}
    second = {"fields": ["b"]}
    memory.save_schema_record("schema_1", first, rationale="r1")
    memory.save_schema_record("schema_2", second, rationale="r2")
    doc = Document(doc_id="doc2", text="dummy")

    # Stub LLM to pick the second schema (choice=2)
    response_content = json.dumps({"choice": 2, "new_schema": None})
    monkeypatch.setattr(
        llm_gateway,
        "chat_completions",
        lambda **kwargs: {"choices": [{"message": {"content": response_content}}]},
    )

    schema = choose_schema(doc, memory)
    assert schema == second

    # Memory should remain unchanged
    assert len(memory.list_schema_records()) == 2


def test_choose_schema_invalid_json(monkeypatch):
    memory = InMemoryStore()
    doc = Document(doc_id="doc3", text="dummy")

    # Stub LLM to return invalid JSON
    monkeypatch.setattr(
        llm_gateway,
        "chat_completions",
        lambda **kwargs: {"choices": [{"message": {"content": "not-json"}}]},
    )
    with pytest.raises(json.JSONDecodeError):
        choose_schema(doc, memory)