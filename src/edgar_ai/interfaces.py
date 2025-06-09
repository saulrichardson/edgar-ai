"""Typed Pydantic models that define the I/O contracts between services.

Replacing the previous `dataclass` versions with `pydantic.BaseModel` adds:

• Runtime validation & type coercion.
• `.model_dump()` / `.model_dump_json()` helpers for persistence & logging.
• Identical attribute access so existing service code remains unchanged.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
    """Rich metadata for a schema field."""

    name: str
    description: str = ""
    rationale: str = ""
    required: bool = True


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


class CriticNote(BaseModel):
    """Feedback from the critic persona on extracted rows."""

    message: str
    severity: str = "info"


class GovernorDecision(BaseModel):
    """Final adjudication of the pipeline outcome for a given document batch."""

    approved: bool
    reasoning: str
