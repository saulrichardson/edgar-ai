"""Schema utilities for Edgar-AI."""

from typing import Dict, List, Any
from interfaces.models import Schema, FieldMeta


def merge_schemas(base: Schema, updates: Schema) -> Schema:
    """
    Merge two schemas, with updates taking precedence.
    
    Args:
        base: Base schema
        updates: Schema with updates
        
    Returns:
        Merged schema
    """
    # Create field map
    base_fields = {f.name: f for f in base.fields}
    
    # Apply updates
    for field in updates.fields:
        base_fields[field.name] = field
    
    # Create merged schema
    return Schema(
        id=f"{base.id}_merged",
        goal_id=base.goal_id,
        name=updates.name or base.name,
        description=updates.description or base.description,
        fields=list(base_fields.values()),
        version=updates.version,
        parent_id=base.id
    )


def validate_schema_compatibility(old: Schema, new: Schema) -> Dict[str, Any]:
    """
    Check if new schema is backward compatible with old schema.
    
    Args:
        old: Previous schema version
        new: New schema version
        
    Returns:
        Compatibility report
    """
    old_required = {f.name for f in old.fields if f.required}
    new_required = {f.name for f in new.fields if f.required}
    
    removed_required = old_required - new_required
    
    return {
        "compatible": len(removed_required) == 0,
        "removed_required_fields": list(removed_required),
        "warnings": []
    }


def generate_json_schema(schema: Schema) -> Dict[str, Any]:
    """
    Generate JSON Schema from Edgar schema.
    
    Args:
        schema: Edgar schema
        
    Returns:
        JSON Schema
    """
    properties = {}
    required = []
    
    for field in schema.fields:
        json_type = _map_to_json_type(field.type)
        
        field_schema = {
            "type": json_type,
            "description": field.description
        }
        
        if field.examples:
            field_schema["examples"] = field.examples
        
        if field.json_schema:
            field_schema.update(field.json_schema)
        
        properties[field.name] = field_schema
        
        if field.required:
            required.append(field.name)
    
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": schema.name,
        "description": schema.description,
        "type": "object",
        "properties": properties,
        "required": required
    }


def _map_to_json_type(edgar_type: str) -> str:
    """Map Edgar field type to JSON Schema type."""
    type_mapping = {
        "text": "string",
        "number": "number",
        "currency": "number",
        "percentage": "number",
        "date": "string",
        "boolean": "boolean",
        "array": "array",
        "object": "object"
    }
    return type_mapping.get(edgar_type, "string")