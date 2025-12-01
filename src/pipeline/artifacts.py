from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from pipeline import models


@dataclass
class PipelineState:
    exhibit_id: str
    goal_text: str | None = None
    schemas: List[models.SchemaVariant] = field(default_factory=list)
    prompts: Dict[str, str] = field(default_factory=dict)         # variant -> prompt text
    extractions: Dict[str, str] = field(default_factory=dict)     # variant -> extraction JSON (string)
    critiques: Dict[str, str] = field(default_factory=dict)       # variant -> critique JSON (string)
    champion: str | None = None
    discoverer_output: str | None = None
    challenger_prompt: str | None = None
    challenger_extraction: str | None = None
    challenger_critique: str | None = None
    governor_decision: str | None = None
    breaker_cases: str | None = None
