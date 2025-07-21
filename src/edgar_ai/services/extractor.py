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

# Settings are imported at runtime so that unit tests can monkeypatch env vars
# before the module is loaded.
from ..config import settings
from ..interfaces import Document, Prompt, Row
from ..utils.schema import schema_to_json_schema
import json as _json


class ExtractorValidationError(RuntimeError):
    """Raised when the LLM returns data that does not respect the schema."""
from ..llm import chat_completions


def _call_gateway(documents: List[Document], prompt: Prompt) -> List[Row]:
    """Call the external LLM gateway to perform extraction via function-calling."""

    rows: List[Row] = []

    for doc in documents:
        messages = [
            {"role": "system", "content": prompt.text},
            {"role": "user", "content": doc.text},
        ]

        attempt = 0
        while True:
            attempt += 1
            try:
                tool_schema = {
                    "type": "function",
                    "function": {
                        "name": "submit_row",
                        "parameters": schema_to_json_schema(prompt.schema_def),
                    },
                }

                response = chat_completions(
                    model=settings.model_extractor,
                    messages=messages,
                    tools=[tool_schema],
                    tool_choice={"type": "function", "function": {"name": "submit_row"}},
                )

                tool_calls = response["choices"][0]["message"].get("tool_calls", [])
                if not tool_calls:
                    raise ValueError("No tool_calls returned")

                args_json = tool_calls[0]["function"]["arguments"]
                data_dict = _json.loads(args_json)

                # ----------------------------------------------------------
                # Light-weight validation (optional)                      
                # ----------------------------------------------------------
                js_schema = schema_to_json_schema(prompt.schema_def)
                if settings.extractor_validation:
                    required_keys = set(js_schema.get("required", []))
                    missing = required_keys - data_dict.keys()
                    if missing:
                        raise ExtractorValidationError(
                            f"Missing required field(s) in tool_call: {sorted(missing)}"
                        )

                    # Fill optional fields with None if absent so downstream
                    # consumers can rely on key presence.
                    for opt_key in js_schema["properties"].keys():
                        data_dict.setdefault(opt_key, None)

                # Phase-4: placeholder critic score
                data_dict["critic_score"] = None

                # Extraction succeeded – exit retry loop
                break
            except Exception as exc:  # noqa: BLE001 pragma: no cover
                if attempt >= settings.extractor_max_retries:
                    raise RuntimeError("Extractor LLM call failed") from exc
                # Otherwise retry (back-off could be added later)

        rows.append(
            Row(
                data=data_dict,
                doc_id=doc.doc_id,
                schema=prompt.schema_def,
                metadata=doc.metadata,
            )
        )

    return rows


def run(documents: List[Document], prompt: Prompt) -> List[Row]:  # noqa: D401
    """Extractor that prefers calling the LLM gateway; falls back to stub."""

    if not settings.llm_gateway_url:
        raise RuntimeError("LLM gateway URL not configured; cannot run Extractor")

    return _call_gateway(documents, prompt)
