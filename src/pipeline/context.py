from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Exhibit:
    id: str
    full_text: str
    tokens: int | None = None  # optional


@dataclass
class View:
    label: str
    text: str
    offsets: Tuple[int, int] | None = None  # char offsets in full_text
    provenance: str | None = None


@dataclass
class ExhibitBundle:
    exhibit: Exhibit
    views: List[View]


@dataclass
class ContextSpec:
    mode: str = "full"  # full | head | tail | window | sampled | summary | slices
    max_chars: int | None = None
    windows: List[Tuple[int, int]] | None = None


def build_views(text: str, spec: ContextSpec) -> List[View]:
    if spec.mode == "full" or spec.mode is None:
        return [View(label="full", text=text, offsets=(0, len(text)), provenance="full")]

    if spec.mode == "head":
        n = spec.max_chars or len(text)
        return [View(label="head", text=text[:n], offsets=(0, min(n, len(text))), provenance="head")]

    if spec.mode == "tail":
        n = spec.max_chars or len(text)
        return [View(label="tail", text=text[-n:], offsets=(max(0, len(text) - n), len(text)), provenance="tail")]

    if spec.mode == "window" and spec.windows:
        views = []
        for i, (s, e) in enumerate(spec.windows):
            s2, e2 = max(0, s), min(len(text), e)
            views.append(View(label=f"window_{i}", text=text[s2:e2], offsets=(s2, e2), provenance="window"))
        return views

    # fallback to full if unknown
    return [View(label="full", text=text, offsets=(0, len(text)), provenance="fallback_full")]


def make_bundle(exhibit_id: str, text: str, spec: ContextSpec | None = None) -> ExhibitBundle:
    spec = spec or ContextSpec(mode="full")
    ex = Exhibit(id=exhibit_id, full_text=text, tokens=None)
    views = build_views(text, spec)
    return ExhibitBundle(exhibit=ex, views=views)
