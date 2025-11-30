from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pipeline.context import ExhibitBundle
from pipeline.artifacts import PipelineState


@dataclass
class PersonaSpec:
    name: str
    system_prompt: str
    build_user: Callable[[ExhibitBundle, PipelineState], str]
