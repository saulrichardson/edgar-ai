"""Critic persona.

Current implementation: *stub* that emits an “info/looks good” note for every
row.

Target behaviour (LLM-powered):

1. Retrieve recent error memory for the same `schema` & `exhibit_type`.
2. Grade each row on a 0–1 scale, citing specific cell-level issues.
3. Optionally ingest human-filed issues as high-severity notes.

The output (`CriticNote`) feeds Tutor, Governor, and long-term Memory.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import List, Any, Dict

from ..memory import FileMemoryStore, ErrorRecord
from ..interfaces import CriticNote, Row
from ..clients import llm_gateway
from ..config import settings
from ..utils.paths import get_data_dir

_RUBRIC_PROMPT = """
You are Edgar‑AI’s extraction Critic. Given the JSON schema below, return a structured JSON rubric for grading extracted rows. The rubric should be an object with a single key "rules", whose value is an array of rule objects. Each rule object must have:
- "code": a short UPPER_SNAKE_CASE identifier
- "description": a brief description of what the rule checks
- "severity": one of ["error", "warning", "info"]
Return ONLY valid JSON.

SCHEMA:
{schema}
"""

_RUBRIC_FUNCTION = {
    "name": "generate_rubric",
    "description": "Generate a JSON rubric for schema-based extraction evaluation",
    "parameters": {
        "type": "object",
        "properties": {
            "rules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "description": {"type": "string"},
                        "severity": {"type": "string", "enum": ["error", "warning", "info"]},
                    },
                    "required": ["code", "description", "severity"],
                },
            },
        },
        "required": ["rules"],
    },
}

def _rubric_path(schema_id: str) -> str:
    path = get_data_dir() / "rubrics" / f"{schema_id}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return str(path)

def _load_or_build_rubric(schema_id: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    path = _rubric_path(schema_id)
    if os.path.exists(path):
        return json.loads(open(path, encoding="utf-8").read())
    prompt = _RUBRIC_PROMPT.format(schema=json.dumps(schema, ensure_ascii=False))
    resp = llm_gateway.chat_completions(
        model=settings.model_critic,
        messages=[{"role": "system", "content": prompt}],
        functions=[_RUBRIC_FUNCTION],
        function_call={"name": "generate_rubric"},
    )
    args = resp["choices"][0]["message"]["function_call"]["arguments"]
    rubric = json.loads(args)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rubric, fh, ensure_ascii=False, indent=2)
    return rubric

_CRITIC_PROMPT = """
You are Edgar‑AI’s extraction Critic. Using the rubric and past error history, evaluate each extracted row. Return ONLY a JSON object matching the 'critic' function signature.

RUBRIC:
{rubric}

PAST_ERRORS:
{history}
"""

_CRITIC_FUNCTION = {
    "name": "critic",
    "description": "Evaluate extracted rows against rubric",
    "parameters": {
        "type": "object",
        "properties": {
            "notes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "row_id": {"type": "string"},
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "severity": {"type": "string", "enum": ["error", "warning", "info"]},
                    },
                    "required": ["row_id", "code", "message", "severity"],
                },
            }
        },
        "required": ["notes"],
    },
}

def run(rows: List[Row]) -> List[CriticNote]:
    """LLM-driven Critic: generate or load rubric, evaluate rows, and persist error records."""
    memory = FileMemoryStore()
    if not rows:
        return []

    schema_id = rows[0].schema.name
    exhibit_type = rows[0].metadata.get("exhibit_type", "")

    past = [err.model_dump(mode="json") for err in memory.list_error_records(schema_id, exhibit_type)]

    rubric = _load_or_build_rubric(
        schema_id,
        rows[0].schema.dict() if hasattr(rows[0], 'schema') else {},
    )

    system_msg = _CRITIC_PROMPT.format(
        rubric=json.dumps(rubric, ensure_ascii=False),
        history=json.dumps(past, ensure_ascii=False),
    )
    user_msg = json.dumps([r.data for r in rows], ensure_ascii=False)

    resp = llm_gateway.chat_completions(
        model=settings.model_critic,
        messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        functions=[_CRITIC_FUNCTION],
        function_call={"name": "critic"},
    )
    args = resp["choices"][0]["message"]["function_call"]["arguments"]
    notes_payload = json.loads(args).get("notes", [])
    notes = [CriticNote(**n) for n in notes_payload]

    for note in notes:
        memory.save_error_record(
            ErrorRecord(
                schema_id=schema_id,
                exhibit_type=exhibit_type,
                row_id=note.row_id,
                code=note.code,
                message=note.message,
                severity=note.severity,
            )
        )
    return notes
