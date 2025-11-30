from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class SchemaField(BaseModel):
    name: str
    type: str
    required: bool
    description: str
    evidence_rule: str


class SchemaVariant(BaseModel):
    variant: str  # lean | standard | strict (or other)
    rationale: Optional[str] = None
    risk: Optional[str] = None
    latency: Optional[str] = None
    fields: List[SchemaField]


class PromptArtifact(BaseModel):
    text: str
    variant: str


class ExtractionArtifact(BaseModel):
    variant: str
    text: str  # raw JSON string from extractor


class CritiqueItem(BaseModel):
    field: str
    status: str  # correct | incorrect | uncertain
    rationale: Optional[str] = None
    better_evidence: Optional[str] = None
    suggested_fix: Optional[str] = None


class Critique(BaseModel):
    variant: str
    items: List[CritiqueItem]

    @property
    def score(self) -> int:
        score = 0
        for item in self.items:
            s = (item.status or "").lower()
            if s == "correct":
                score += 1
            elif s == "incorrect":
                score -= 1
        return score

    @property
    def totals(self) -> tuple[int, int, int]:
        correct = sum(1 for i in self.items if (i.status or "").lower() == "correct")
        incorrect = sum(1 for i in self.items if (i.status or "").lower() == "incorrect")
        total = len(self.items)
        return correct, incorrect, total


class RunResult(BaseModel):
    exhibit_id: str
    goal: str
    variants: List[str]
    champion: str
    artifacts_dir: str | None = None
