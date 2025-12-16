from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class GoalBlueprint(BaseModel):
    title: str
    blueprint: str


class SchemaCandidate(BaseModel):
    candidate_id: str
    proposer: str
    schema_payload: Any


class PromptArtifact(BaseModel):
    text: str
    candidate_id: str


class ExtractionArtifact(BaseModel):
    candidate_id: str
    text: str  # raw JSON string from extractor


class CritiqueArtifact(BaseModel):
    candidate_id: str
    critic: str
    text: str  # raw JSON string from critic


class RunResult(BaseModel):
    exhibit_id: str
    goal_id: str
    goal_title: str
    candidates: List[str]
    champion_candidate_id: str
    artifacts_dir: str | None = None
    governor_decision: str | None = None
