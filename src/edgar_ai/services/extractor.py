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
from ..utils.schema import schema_to_json_schema


def _call_gateway(documents: List[Document], prompt: Prompt) -> List[Row]:
    """Call the external LLM gateway to perform extraction via function-calling."""

    from ..clients import llm_gateway  # imported lazily to avoid dependency if unused

    rows: List[Row] = []

    for doc in documents:
        messages = [
            {"role": "system", "content": prompt.text},
            {"role": "user", "content": doc.text},
        ]

        try:
            tool_schema = {
                "type": "function",
                "function": {
                    "name": "submit_row",
                    "parameters": schema_to_json_schema(prompt.schema_def),
                },
            }

            response = llm_gateway.chat_completions(
                model=settings.model_extractor,
                messages=messages,
                tools=[tool_schema],
                tool_choice={"type": "function", "function": {"name": "submit_row"}},
            )

            tool_calls = response["choices"][0]["message"].get("tool_calls", [])
            if not tool_calls:
                raise ValueError("No tool_calls returned")

            args_json = tool_calls[0]["function"]["arguments"]

            import json as _json

            data_dict = _json.loads(args_json)
        except Exception as exc:  # pragma: no cover – surface errors
            raise RuntimeError("Extractor LLM call failed") from exc

        rows.append(Row(data=data_dict, doc_id=doc.doc_id))

    return rows


def run(documents: List[Document], prompt: Prompt) -> List[Row]:  # noqa: D401
    """Extractor that prefers calling the LLM gateway; falls back to stub."""

    if not settings.llm_gateway_url:
        raise RuntimeError("LLM gateway URL not configured; cannot run Extractor")

    return _call_gateway(documents, prompt)
