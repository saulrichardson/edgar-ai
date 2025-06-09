"""Unit tests for the run_pipeline orchestration (schema selection → extraction)."""

import sys
from pathlib import Path

# Ensure src/ is on PYTHONPATH for test imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from edgar_ai.interfaces import Document
from edgar_ai.memory import InMemoryStore
import importlib
run_pipeline_mod = importlib.import_module("edgar_ai.pipeline.run_pipeline")
from edgar_ai.pipeline.run_pipeline import run_pipeline


def test_run_pipeline_flows_through_choose_and_extract(monkeypatch):
    """Should invoke choose_schema then extract, returning extractor rows and saving schema."""
    memory = InMemoryStore()
    doc = Document(doc_id="doc1", text="dummy text")
    fake_schema = {"fields": ["x"]}
    fake_rows = [{"x": "y"}]

    def fake_choose_schema(d, m):
        assert d is doc
        assert m is memory
        # mimic cold-start saving behavior
        m.save_schema_record("schema_1", fake_schema, rationale=d.text)
        return fake_schema

    # Stub schema selection used by run_pipeline (captured at import time)
    monkeypatch.setattr(run_pipeline_mod, "choose_schema", fake_choose_schema)

    def fake_extract(d, s):
        assert d is doc
        assert s == fake_schema
        return fake_rows

    # Stub the extractor used by run_pipeline (captured at import time)
    monkeypatch.setattr(run_pipeline_mod, "extract", fake_extract)

    result = run_pipeline(doc, memory)
    assert result == fake_rows
    records = memory.list_schema_records()
    assert len(records) == 1
    assert records[0].schema == fake_schema