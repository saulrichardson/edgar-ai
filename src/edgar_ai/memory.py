"""Concurrency-safe file-backed memory for rich extraction schemas.

This version stores only the *current* schema format (fields mapping with
type/description/rationale) – no legacy list support and no stub paths.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

from edgar_ai.utils.paths import get_data_dir

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class SchemaRecord(BaseModel):
    """A stored extraction schema with per-field metadata."""

    schema_id: str
    schema_def: dict = Field(alias="schema")
    rationale: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: int = 5  # bump for FieldMeta list

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }

class ErrorRecord(BaseModel):
    """A past CriticNote (or failing row) for recall by the Critic."""

    schema_id: str
    exhibit_type: str
    row_id: str
    code: str
    message: str
    severity: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }


# ---------------------------------------------------------------------------
# Storage implementation (file-backed with filelock)
# ---------------------------------------------------------------------------


try:
    from filelock import FileLock  # type: ignore

    _Lock = FileLock
except ModuleNotFoundError:  # pragma: no cover

    class _Dummy:  # type: ignore
        def __init__(self, *_a, **_kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

    _Lock = _Dummy


class FileMemoryStore:  # noqa: D101 – simple persistence helper
    _FILENAME = "memory.json"

    def __init__(self) -> None:
        self._path: Path = get_data_dir().joinpath(self._FILENAME)
        self._lock = _Lock(str(self._path) + ".lock")

    # ---------------- internal helpers ----------------

    def _load_all(self) -> tuple[list[dict], list[dict]]:
        """Read memory.json and return (schema_objs, error_record_objs)."""
        if not self._path.exists():
            return [], []
        raw = json.loads(self._path.read_text(encoding="utf-8"))

        # Legacy: raw list == old schema records
        if isinstance(raw, list):
            return raw, []

        if not isinstance(raw, dict):
            raise RuntimeError("memory.json must be a JSON object or array")

        schemas = raw.get("schema_records", [])
        errors = raw.get("critic_errors", [])
        return schemas, errors

    def _save_all(
        self,
        schema_records: list[SchemaRecord],
        error_records: list[ErrorRecord],
    ) -> None:
        """Write combined memory.json with schemas + critic_errors."""
        data = {
            "schema_records": [r.model_dump(mode="json") for r in schema_records],
            "critic_errors": [r.model_dump(mode="json") for r in error_records],
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp.replace(self._path)

    def _save(self, records: List[SchemaRecord]) -> None:
        """Persist only schema_records, preserving any existing critic_errors."""
        schemas, errors = self._load_all()
        self._save_all(records, [ErrorRecord(**e) for e in errors])

    # ---------------- public API ----------------

    def save_schema_record(self, schema_id: str, schema: dict, rationale: str) -> None:  # noqa: D401
        with self._lock:
            schema_objs, error_objs = self._load_all()
            # dedupe by schema_id and append new
            schema_objs = [r for r in schema_objs if r.get("schema_id") != schema_id]
            schema_objs.append(
                SchemaRecord(schema_id=schema_id, schema_def=schema, rationale=rationale).model_dump(mode="json")
            )
            self._save_all(
                [SchemaRecord(**r) for r in schema_objs],
                [ErrorRecord(**e) for e in error_objs],
            )



    def list_schema_records(self) -> List[SchemaRecord]:  # noqa: D401
        with self._lock:
            schema_objs, _ = self._load_all()
            return [SchemaRecord(**obj) for obj in schema_objs]

    def delete_schema_record(self, schema_id: str) -> bool:  # noqa: D401
        with self._lock:
            schema_objs, error_objs = self._load_all()
            new_schemas = [r for r in schema_objs if r.get("schema_id") != schema_id]
            if len(new_schemas) == len(schema_objs):
                return False
            self._save_all(
                [SchemaRecord(**r) for r in new_schemas],
                [ErrorRecord(**e) for e in error_objs],
            )
            return True

    def list_error_records(self, schema_id: str, exhibit_type: str) -> List[ErrorRecord]:
        """Return saved ErrorRecord entries for the given schema_id+exhibit_type."""
        with self._lock:
            _, error_objs = self._load_all()
        return [
            ErrorRecord(**obj)
            for obj in error_objs
            if obj.get("schema_id") == schema_id and obj.get("exhibit_type") == exhibit_type
        ]

    def save_error_record(self, record: ErrorRecord) -> None:
        """Persist a new ErrorRecord (deduped if needed)."""
        with self._lock:
            schema_objs, error_objs = self._load_all()
            error_objs.append(record.model_dump(mode="json"))
            self._save_all(
                [SchemaRecord(**r) for r in schema_objs],
                [ErrorRecord(**e) for e in error_objs],
            )
