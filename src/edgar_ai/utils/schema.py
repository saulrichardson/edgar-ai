"""Utility helpers related to Schema objects."""

from __future__ import annotations

from typing import Dict

from ..interfaces import Schema


def schema_to_json_schema(schema: Schema) -> Dict:
    """Convert an internal *Schema* into JSON-Schema for OpenAI function calling."""

    properties = {name: {"type": "string"} for name in schema.fields}

    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
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
