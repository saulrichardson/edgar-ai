"""Unit tests for the in-memory schema MemoryStore implementation."""

import sys
from pathlib import Path

# Ensure src/ is on PYTHONPATH for test imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

import pytest

from edgar_ai.memory import InMemoryStore, MemoryStore, SchemaRecord


def test_in_memory_store_implements_interface():
    store: MemoryStore = InMemoryStore()
    assert isinstance(store, MemoryStore)


def test_list_empty_records():
    store = InMemoryStore()
    assert store.list_schema_records() == []


def test_save_and_list_records():
    store = InMemoryStore()
    data = {"overview": "test", "topics": ["a"], "fields": ["f1", "f2"]}
    store.save_schema_record("id1", data, rationale="rationale1")
    records = store.list_schema_records()
    assert len(records) == 1
    record = records[0]
    assert isinstance(record, SchemaRecord)
    assert record.schema_id == "id1"
    assert record.schema == data
    assert record.rationale == "rationale1"


def test_multiple_records_ordered():
    store = InMemoryStore()
    store.save_schema_record("id1", {}, rationale="r1")
    store.save_schema_record("id2", {}, rationale="r2")
    ids = [r.schema_id for r in store.list_schema_records()]
    assert ids == ["id1", "id2"]