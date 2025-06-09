"""Unit tests for the extractor step of the pipeline."""

import sys
from pathlib import Path

# Ensure src/ is on PYTHONPATH for test imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

import json
import pytest

from edgar_ai.interfaces import Document
from edgar_ai.clients import llm_gateway
from edgar_ai.pipeline.extractor import extract


def test_extract_success(monkeypatch):
    """Should parse valid JSON from the LLM response into row dictionaries."""
    fake_content = json.dumps([{"field1": "value1"}])

    def fake_chat_completions(**kwargs):
        return {"choices": [{"message": {"content": fake_content}}]}

    monkeypatch.setattr(llm_gateway, "chat_completions", fake_chat_completions)

    doc = Document(doc_id="d1", text="dummy text")
    schema = {"fields": ["field1"]}
    rows = extract(doc, schema)
    assert isinstance(rows, list)
    assert rows == [{"field1": "value1"}]


def test_extract_invalid_json(monkeypatch):
    """Should return an empty list if the LLM returns invalid JSON."""
    def fake_chat_completions(**kwargs):
        return {"choices": [{"message": {"content": "nope"}}]}

    monkeypatch.setattr(llm_gateway, "chat_completions", fake_chat_completions)

    doc = Document(doc_id="d2", text="dummy text")
    schema = {"fields": ["field1"]}
    rows = extract(doc, schema)
    assert rows == []