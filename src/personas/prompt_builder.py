from __future__ import annotations

import json
from typing import List, Dict

from pipeline import models

SYSTEM_PROMPT = (
    "You are Prompt-Builder++. Given a schema (JSON), craft a deterministic extraction prompt for an LLM Extractor. "
    "Be concise but complete. Requirements: \n"
    "- Role/task statement.\n"
    "- Output: JSON array with single object; include per-field evidence key named <field>_evidence.\n"
    "- Per-field rules: what to extract, type/format, normalization, evidence rule.\n"
    "- Evidence must be quoted snippet; if missing, set value and evidence to null.\n"
    "- No extra commentary; return prompt text only."
)


def build_user_message(schema_variant: models.SchemaVariant) -> str:
    schema_json = json.dumps(schema_variant.dict(), ensure_ascii=False, indent=2)
    return f"Schema:\n{schema_json}\nWrite the final prompt."
