"""Schema synthesizer service.

Creates a *Schema* object from discovered field candidates.
"""

from __future__ import annotations

from typing import List

from ..interfaces import FieldCandidate, Schema, FieldMeta
from ..config import settings
from ..llm import chat_completions, is_simulate_mode


_SYSTEM_PROMPT = """You are a schema synthesis assistant.\n\nGiven an array of field names, design a JSON Schema (draft-07) object that describes a flat object containing exactly those fields.\n\nFor each field, infer a likely JSON type (string, number, integer, boolean) and add a short description.\n\nReturn ONLY the JSON Schema object.\n"""


def _synth_via_llm(fields: List[str]) -> Schema:  # noqa: D401
    import json as _json, hashlib

    rsp = chat_completions(
        model=settings.model_schema_synth,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _json.dumps(fields)},
        ],
        temperature=settings.schema_synth_temperature,
    )

    content = rsp["choices"][0]["message"]["content"].strip()

    try:
        schema_json = _json.loads(content)
    except Exception:
        # fallback: simple schema
        schema_json = {
            "type": "object",
            "properties": {f: {"type": "string"} for f in fields},
            "required": fields,
        }

    # Convert to internal Schema object
    field_meta: List[FieldMeta] = []
    props = schema_json.get("properties", {}) if isinstance(schema_json, dict) else {}
    for name in fields:
        prop = props.get(name, {}) if isinstance(props, dict) else {}
        field_meta.append(
            FieldMeta(
                name=name,
                description=prop.get("description"),
                json_schema=prop if prop else None,
                required=name in schema_json.get("required", []),
            )
        )

    sha = hashlib.sha256(_json.dumps(schema_json, sort_keys=True).encode()).hexdigest()[:10]
    return Schema(name=f"schema_{sha}", fields=field_meta)


def run(candidates: List[FieldCandidate]) -> Schema:  # noqa: D401
    """Turn *candidates* into a Schema via LLM (or deterministic fallback)."""

    field_names = list({c.field_name for c in candidates})

    if is_simulate_mode():
        return Schema(name="sim_schema", fields=[FieldMeta(name=n) for n in field_names])

    return _synth_via_llm(field_names)
