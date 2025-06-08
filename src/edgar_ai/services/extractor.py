"""Extractor persona.

Behaviour matrix:

| Mode                          | Trigger                                   | Outcome                          |
| ----------------------------- | ----------------------------------------- | -------------------------------- |
| **LLM mode (preferred)**      | `settings.llm_gateway_url` is configured  | Calls gateway → returns real JSON |
| **Offline / stub mode**       | No gateway URL or gateway failure         | Returns deterministic sample row |

Once Prompt-Builder produces a function-calling prompt, the block `_call_gateway` will parse the structured `tool_calls` array to build `Row` objects.
"""

from __future__ import annotations

from typing import List

from ..config import settings
from ..interfaces import Document, Prompt, Row


def _stub_rows(documents: List[Document]) -> List[Row]:
    """Deterministic stub for environments without LLM connectivity."""

    return [
        Row(
            data={
                "company_name": "Example Corp",
                "report_type": "10-K",
                "fiscal_year": "2023",
            },
            doc_id=doc.doc_id,
        )
        for doc in documents
    ]


def _call_gateway(documents: List[Document], prompt: Prompt) -> List[Row]:
    """Call the external LLM gateway to perform extraction via function-calling."""

    from ..clients import llm_gateway  # imported lazily to avoid dependency if unused

    rows: List[Row] = []

    for doc in documents:
        messages = [
            {"role": "system", "content": prompt.text},
            {"role": "user", "content": doc.html},
        ]

        try:
            response = llm_gateway.chat_completions(
                model="gpt-3.5-turbo-0613",
                messages=messages,
                tools=None,
            )

            # naive parsing – for a function call we'd pull from tool_calls; here
            # we expect assistant content to be JSON.
            choices = response.get("choices", [])
            content = choices[0]["message"]["content"] if choices else "{}"
            import json as _json

            data = _json.loads(content)
        except Exception:  # noqa: BLE001  – fall back to stub on any error
            return _stub_rows(documents)

        rows.append(Row(data=data, doc_id=doc.doc_id))

    return rows


def run(documents: List[Document], prompt: Prompt) -> List[Row]:  # noqa: D401
    """Extractor that prefers calling the LLM gateway; falls back to stub."""

    if settings.llm_gateway_url:
        try:
            return _call_gateway(documents, prompt)
        except Exception:  # pragma: no cover
            # gateway misbehaved – use stub
            return _stub_rows(documents)

    # default stub path for offline/dev mode
    return _stub_rows(documents)
