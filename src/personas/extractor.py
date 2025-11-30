from __future__ import annotations

from typing import List, Dict


def messages(prompt_text: str, exhibit_text: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": f"EXHIBIT:\n<<<\n{exhibit_text}\n>>>"},
    ]
