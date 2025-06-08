"""Tutor service.

Would normally take critic feedback and improve the model. Here it's a NOP.
"""


from typing import List

from ..interfaces import CriticNote


def run(notes: List[CriticNote]) -> None:  # noqa: D401
    """A no-op stub."""

    # Intentionally do nothing – returns None.
