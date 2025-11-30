from __future__ import annotations

from typing import List, Dict

from clients.gateway import GatewayConfig

SYSTEM_PROMPT = (
    "You are Goal-Setter. Read any business/legal exhibit and pick the single highest-value "
    "analytical goal for downstream extraction. Output a compact blueprint: (a) problem statement; "
    "(b) target entities/rows; (c) key facts to extract; (d) evidence expectations (traceable "
    "quotes/sections); (e) success criteria. Keep it domain-agnostic and don’t design schemas."
)


def build_user_message(exhibit_text: str) -> str:
    return f"Task: choose the best extraction goal for the exhibit below.\n\nEXHIBIT:\n<<<\n{exhibit_text}\n>>>"


def messages(user_content: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
