"""Utility helpers related to Schema objects."""

from __future__ import annotations

from typing import Dict

from ..interfaces import Schema, FieldMeta


def schema_to_json_schema(schema: Schema) -> Dict:  # noqa: D401
    """Convert an internal *Schema* into JSON-Schema for OpenAI function calling."""

    properties: Dict[str, Dict] = {}
    required: list[str] = []

    for field in schema.fields:
        if isinstance(field, FieldMeta):
            if field.json_schema:
                properties[field.name] = field.json_schema
            else:
                properties[field.name] = {"type": "string", "description": field.description}

            if field.required:
                required.append(field.name)
        else:  # pragma: no cover – legacy string
            properties[str(field)] = {"type": "string"}
            required.append(str(field))

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _dtype_to_json_type(dtype: str) -> str:
    # Very small mapping; extend as needed.
    mapping = {
        "string": "string",
        "number": "number",
        "integer": "integer",
        "bool": "boolean",
    }
    return mapping.get(dtype, "string")
