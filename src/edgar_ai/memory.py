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
    """One stored extraction schema (rich field metadata)."""

    schema_id: str
    # Alias 'schema' for on-disk key consistency, but use attribute name
    # 'schema_def' in Python to avoid pydantic BaseModel.schema clash.
    schema_def: dict = Field(alias="schema")
    rationale: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: int = 3

    model_config = {"populate_by_name": True}


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

    def _load(self) -> List[SchemaRecord]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise RuntimeError("memory.json must be a JSON array")
        return [SchemaRecord(**obj) for obj in raw]

    def _save(self, records: List[SchemaRecord]) -> None:
        serialisable = [r.model_dump(by_alias=True, mode="json") for r in records]
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(serialisable, ensure_ascii=False, indent=2))
        tmp.replace(self._path)

    # ---------------- public API ----------------

    def save_schema_record(self, schema_id: str, schema: dict, rationale: str) -> None:  # noqa: D401
        with self._lock:
            records = self._load()
            records = [r for r in records if r.schema_id != schema_id]
            records.append(SchemaRecord(schema_id=schema_id, schema_def=schema, rationale=rationale))
            self._save(records)

    def list_schema_records(self) -> List[SchemaRecord]:  # noqa: D401
        with self._lock:
            return self._load()

    def delete_schema_record(self, schema_id: str) -> bool:  # noqa: D401
        with self._lock:
            records = self._load()
            new_records = [r for r in records if r.schema_id != schema_id]
            if len(new_records) == len(records):
                return False
            self._save(new_records)
            return True