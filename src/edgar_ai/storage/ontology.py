"""In-memory ontology registry.

For a real project this would interface with a graph database to store entity
relationships. The scaffold keeps everything in a Python dict.
"""

from __future__ import annotations

from typing import Dict, List


_ONTOLOGY: Dict[str, List[str]] = {}


def add_relation(entity: str, related: str) -> None:  # noqa: D401
    _ONTOLOGY.setdefault(entity, []).append(related)


def get_relations(entity: str) -> List[str]:  # noqa: D401
    return _ONTOLOGY.get(entity, [])
