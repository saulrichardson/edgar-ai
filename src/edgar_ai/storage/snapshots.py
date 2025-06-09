"""Helpers to persist prompts and extracted rows for offline inspection.

These functions are *side-effect* utilities – they do **not** participate in
the main data-flow of the pipeline but are invaluable for debugging and later
evaluation.  By keeping them isolated here we avoid cluttering the core
storage interfaces (ledger, raw_lake, etc.).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ..interfaces import Prompt, Row
from ..utils.paths import get_data_dir

__all__ = ["save_prompt", "save_rows", "save_response"]


def save_response(doc_id: str, schema_hash: str, raw_response: str) -> Path:  # noqa: D401
    """Persist raw LLM JSON/text to *responses/<doc_id>-<schema_hash>.json*.

    This allows offline diffing between prompt & response.
    """

    file_path = _ensure_dir("responses").joinpath(f"{doc_id}-{schema_hash}.json")
    file_path.write_text(raw_response, encoding="utf-8")
    return file_path


def _ensure_dir(sub: str) -> Path:  # noqa: D401
    """Return *data_dir/sub* creating it if necessary."""

    path = get_data_dir().joinpath(sub)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_prompt(prompt: Prompt, schema_hash: str) -> Path:  # noqa: D401
    """Persist *prompt.text* under *prompts/<schema_hash>.txt*.

    Returns the path that was written so callers may log it.
    """

    file_path = _ensure_dir("prompts").joinpath(f"{schema_hash}.txt")
    file_path.write_text(prompt.text, encoding="utf-8")
    return file_path


def save_rows(doc_id: str, rows: List[Row]) -> Path:  # noqa: D401
    """Write Row objects as JSON Lines to *rows/<doc_id>.jsonl*.

    Each line is the ``Row.data`` mapping so the file is human-friendly and
    easy to load back into pandas.
    """

    file_path = _ensure_dir("rows").joinpath(f"{doc_id}.jsonl")

    with file_path.open("w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row.data, ensure_ascii=False))
            fp.write("\n")

    return file_path
