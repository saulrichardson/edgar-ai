from __future__ import annotations

from typing import List, Dict

from pipeline.context import ExhibitBundle


def build_user_message(bundle: ExhibitBundle) -> str:
    view = bundle.views[0]
    return f"EXHIBIT:\n<<<\n{view.text}\n>>>"
