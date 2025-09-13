"""Core data models for Edgar-AI."""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# Document Models
class DocumentMetadata(BaseModel):
    """Metadata for a document."""
    source: str
    form_type: Optional[str] = None
    filing_date: Optional[str] = None
    company: Optional[str] = None
    cik: Optional[str] = None
    accession_number: Optional[str] = None
    url: Optional[str] = None


class Document(BaseModel):
    """Input document for processing."""
    id: str
    text: str
    metadata: Optional[DocumentMetadata] = None


# Goal Models
class FieldCandidate(BaseModel):
    """Potential field discovered in documents."""
    name: str
    type: str
    description: Optional[str] = None
    occurrence_count: int = 1
    examples: List[str] = Field(default_factory=list)


class Goal(BaseModel):
    """Extraction goal determined by Goal Setter."""
    goal_id: str
    overview: str
    topics: List[str]
    fields: List[FieldCandidate]


# Schema Models  
class FieldMeta(BaseModel):
    """Rich metadata for a schema field."""
    name: str
    type: Literal["text", "number", "currency", "percentage", "date", "boolean", "array", "object"]
    description: str
    required: bool = True
    examples: List[str] = Field(default_factory=list)
    json_schema: Optional[Dict[str, Any]] = None  # For complex types
    validation_rules: List[str] = Field(default_factory=list)


class Schema(BaseModel):
    """Structured schema for extraction."""
    id: str
    goal_id: str
    name: str
    description: str
    fields: List[FieldMeta]
    version: str = "1.0.0"
    created_at: Optional[datetime] = None
    parent_id: Optional[str] = None  # For schema evolution


# Prompt Models
class Prompt(BaseModel):
    """Extraction prompt with schema."""
    id: Optional[str] = None
    schema_id: str
    system_prompt: str
    user_prompt: str
    function_schema: Dict[str, Any]
    token_budget: int = 100000


# Extraction Models
class Row(BaseModel):
    """Single row of extracted data."""
    schema_id: Optional[str] = None
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Feedback Models
class CriticNote(BaseModel):
    """Feedback from the Critic."""
    row_index: int
    field_name: str
    score: Optional[float] = None  # 0.0 to 1.0
    feedback: str
    suggestion: str
    severity: Literal["info", "warning", "error"] = "info"


class GovernorDecision(BaseModel):
    """Decision from the Governor."""
    status: Literal["approved", "conditional", "rejected"]
    quality_score: float
    actions: List[str] = Field(default_factory=list)
    feedback: str


# Result Models
class ExtractionResult(BaseModel):
    """Complete extraction result."""
    document_id: str
    goal: Goal
    schema: Schema
    rows: List[Row]
    critic_notes: List[CriticNote]
    decision: GovernorDecision
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Learning Models
class ErrorRecord(BaseModel):
    """Record of an extraction error."""
    field: str
    error_type: str
    context: Dict[str, Any]
    timestamp: datetime


class Improvement(BaseModel):
    """Suggested improvement from Tutor."""
    schema_id: str
    prompt_id: Optional[str] = None
    description: str
    changes: List[str]
    expected_impact: str
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)


class SchemaVersion(BaseModel):
    """Schema version information."""
    version: str
    changes: List[str]
    backward_compatible: bool
    migration_script: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Gateway Models
class ChatMessage(BaseModel):
    """Chat message for LLM communication."""
    role: Literal["system", "user", "assistant", "function"]
    content: str
    function_call: Optional[Dict[str, Any]] = None


class LLMRequest(BaseModel):
    """Request to LLM gateway."""
    model: str
    messages: List[ChatMessage]
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Response from LLM gateway."""
    id: str
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]
    metadata: Dict[str, Any] = Field(default_factory=dict)