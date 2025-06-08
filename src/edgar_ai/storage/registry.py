"""Simple registry mapping names to objects (akin to a service locator)."""

from __future__ import annotations

from typing import Any, Dict


_REGISTRY: Dict[str, Any] = {}


def register(name: str, obj: Any) -> None:  # noqa: D401
    _REGISTRY[name] = obj


def get(name: str) -> Any | None:  # noqa: D401
    return _REGISTRY.get(name)


def all() -> Dict[str, Any]:  # noqa: D401
    return dict(_REGISTRY)
