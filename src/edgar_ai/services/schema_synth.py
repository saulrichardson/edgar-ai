"""Schema synthesizer service.

Creates a *Schema* object from discovered field candidates.
"""

from __future__ import annotations

from typing import List

from ..interfaces import FieldCandidate, Schema


def run(candidates: List[FieldCandidate]) -> Schema:  # noqa: D401
    """Return a schema comprising unique candidate field names."""

    field_names = list({c.field_name for c in candidates})
    return Schema(name="stub_schema", fields=field_names)
