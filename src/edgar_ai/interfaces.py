"""Typed Pydantic models that define the I/O contracts between services.

Replacing the previous `dataclass` versions with `pydantic.BaseModel` adds:

• Runtime validation & type coercion.
• `.model_dump()` / `.model_dump_json()` helpers for persistence & logging.
• Identical attribute access so existing service code remains unchanged.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from datetime import datetime


class Document(BaseModel):
    """Pre-processed exhibit text delivered to the pipeline."""

    doc_id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FieldCandidate(BaseModel):
    """Represents a potential (key, value) pair discovered in a document."""

    field_name: str
    raw_value: str
    confidence: float = 1.0




class FieldMeta(BaseModel):
    """Rich metadata for a schema field (domain-agnostic)."""

    name: str
    description: str = ""
    rationale: str = ""
    required: bool = True
    # Optional JSON-Schema fragment defining nested structure / data type.
    json_schema: Dict[str, Any] | None = None


class Schema(BaseModel):
    """Describes the structured schema expected for extraction."""

    name: str
    fields: List[FieldMeta]


class Prompt(BaseModel):
    """Prompt that will be sent to an LLM extractor."""

    text: str
    schema_def: Schema  # renamed from `schema` to avoid pydantic shadow warning


class Row(BaseModel):
    """A structured row of extracted data which matches *Schema* definition."""

    data: Dict[str, Any]
    doc_id: Optional[str] = None

    # Optional attachments used by downstream personas (Critic, Governor, etc.)
    # They are kept optional so existing callers that only care about the raw
    # data do not need to pass them.  Critic will fall back gracefully if they
    # are missing but having them here avoids dynamic attribute hacks.
    schema: Optional["Schema"] = None  # forward-declared above
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CriticNote(BaseModel):
    """Feedback from the critic persona on an extracted row.

    The schema purposefully matches the structure produced by
    ``services.critic.run`` so downstream actors (Governor, Tutor, Memory)
    can rely on the presence of every attribute.  Keeping the model here in
    *interfaces.py* avoids circular imports and provides runtime validation
    across the application.
    """

    row_id: str
    code: str
    message: str
    severity: str = "info"


class SchemaCritique(BaseModel):
    """A critique of a JSON schema against high-level design principles."""

    principle: str
    score: float
    message: str
    schema_id: str
    created_at: datetime


class GovernorDecision(BaseModel):
    """Final adjudication of the pipeline outcome for a given document batch."""

    approved: bool
    reasoning: str
