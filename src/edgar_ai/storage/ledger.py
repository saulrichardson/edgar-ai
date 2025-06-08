"""Ledger: stores structured rows extracted from documents."""

from __future__ import annotations

from typing import Dict, List

from ..interfaces import Row


_LEDGER: Dict[str, List[Row]] = {}


def add_row(doc_id: str, row: Row) -> None:  # noqa: D401
    _LEDGER.setdefault(doc_id, []).append(row)


def get_rows(doc_id: str) -> List[Row]:  # noqa: D401
    return _LEDGER.get(doc_id, [])


def all_rows() -> Dict[str, List[Row]]:  # noqa: D401
    return _LEDGER
