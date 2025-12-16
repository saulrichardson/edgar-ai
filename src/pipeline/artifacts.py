from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class PipelineState:
    exhibit_id: str
    goal: Dict[str, Any] | None = None
    candidates: Dict[str, Any] = field(default_factory=dict)  # candidate_id -> schema JSON
    prompts: Dict[str, str] = field(default_factory=dict)  # candidate_id -> prompt text
    extractions: Dict[str, str] = field(default_factory=dict)  # candidate_id -> extraction JSON (string)
    critiques: Dict[str, Dict[str, str]] = field(default_factory=dict)  # candidate_id -> critic -> critique JSON
    champion_candidate_id: str | None = None
    discoverer_output: str | None = None
    challenger_candidate_id: str | None = None
    governor_decision: str | None = None
    breaker_cases: str | None = None
