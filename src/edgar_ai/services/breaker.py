"""Breaker service.

Stress-tests the system with adversarial prompts or edge-case inputs. Not used
in the scaffold besides returning a static boolean.
"""

from __future__ import annotations

from typing import List

from ..interfaces import Row


def run(rows: List[Row]) -> bool:  # noqa: D401
    """Always returns *False* indicating no breakage discovered."""

    return False
