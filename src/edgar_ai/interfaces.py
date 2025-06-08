"""Typed dataclasses that define the I/O contracts between services.

These classes are intentionally minimal for the scaffold stage. Fields can be
extended later as the pipeline becomes more sophisticated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    """A raw or pre-processed document originating from EDGAR or elsewhere."""

    doc_id: str
    html: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldCandidate:
    """Represents a potential (key, value) pair discovered in a document."""

    field_name: str
    raw_value: str
    confidence: float = 1.0


@dataclass
class Schema:
    """Describes the structured schema expected for extraction."""

    name: str
    fields: List[str]


@dataclass
class Prompt:
    """Prompt that will be sent to an LLM extractor."""

    text: str
    schema: Schema


@dataclass
class Row:
    """A structured row of extracted data which matches *Schema* definition."""

    data: Dict[str, Any]
    doc_id: Optional[str] = None


@dataclass
class CriticNote:
    """Feedback from the critic persona on extracted rows."""

    message: str
    severity: str = "info"


@dataclass
class GovernorDecision:
    """Final adjudication of the pipeline outcome for a given document batch."""

    approved: bool
    reasoning: str
