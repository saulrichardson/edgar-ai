"""Thin sync client for the local gateway /v1/responses endpoint.

Designed for deterministic persona pipelines: always streams, accumulates text output.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import httpx


@dataclass
class GatewayConfig:
    url: str = "http://127.0.0.1:8000/v1/responses"
    model: str = "openai:gpt-5"
    reasoning_effort: str = "medium"
    timeout_seconds: float = 180.0


def _extract_output_text(events: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    saw_delta = False
    for evt in events:
        t = evt.get("type")
        if t == "response.output_text.delta":
            saw_delta = True
            parts.append(evt.get("delta", ""))
        elif t == "response.output_text.done":
            # OpenAI streams often send a final `done` event that contains the full
            # accumulated text. If we've already collected deltas, appending `text`
            # will duplicate the output.
            if not saw_delta:
                parts.append(evt.get("text", ""))
        elif t == "response.completed" and not parts:
            # Non-OpenAI providers (or some stream variants) may not emit output_text events.
            response = evt.get("response") or {}
            output_text = response.get("output_text")
            if isinstance(output_text, list):
                parts.append("".join(str(chunk) for chunk in output_text))
            elif isinstance(output_text, str):
                parts.append(output_text)
    return "".join(parts).strip()


def send_chat(
    messages: List[Dict[str, str]],
    config: GatewayConfig,
    *,
    stream: bool = True,
    response_format: Dict[str, Any] | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
) -> str:
    """Send chat messages to the gateway and return concatenated output text.

    The gateway only supports streaming. We parse SSE-style data lines and collect text deltas.
    """
    if os.getenv("EDGAR_AI_SIMULATE", "").lower() in {"1", "true", "yes"}:
        return _simulate_chat(messages)

    payload: Dict[str, Any] = {
        "model": config.model,
        "reasoning": {"effort": config.reasoning_effort},
        "stream": stream,
        "input": messages,
    }
    if response_format is not None:
        payload["response_format"] = response_format
    if temperature is not None:
        payload["temperature"] = temperature
    if max_output_tokens is not None:
        payload["max_output_tokens"] = max_output_tokens

    events: List[Dict[str, Any]] = []
    with httpx.stream(
        "POST",
        config.url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=config.timeout_seconds,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            if isinstance(line, bytes):
                if not line.startswith(b"data: "):
                    continue
                raw = line[len(b"data: ") :]
                try:
                    evt = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                events.append(evt)
                continue

            if isinstance(line, str):
                if not line.startswith("data: "):
                    continue
                raw = line[len("data: ") :]
                # OpenAI-style streams may send a terminal marker like "[DONE]".
                if raw.strip() == "[DONE]":
                    continue
                try:
                    evt = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                events.append(evt)
    return _extract_output_text(events)


def _simulate_chat(messages: List[Dict[str, str]]) -> str:
    system = (messages[0].get("content") if messages else "") or ""
    user = (messages[-1].get("content") if messages else "") or ""

    def _extract_json_from_text(text: str) -> Any:
        s = (text or "").strip()
        try:
            return json.loads(s)
        except Exception:
            pass
        first_obj = s.find("{")
        first_arr = s.find("[")
        if first_obj == -1 and first_arr == -1:
            return None
        if first_obj != -1 and (first_arr == -1 or first_obj < first_arr):
            start = first_obj
            end = s.rfind("}")
        else:
            start = first_arr
            end = s.rfind("]")
        if end <= start:
            return None
        try:
            return json.loads(s[start : end + 1])
        except Exception:
            return None

    if "You are Goal-Router" in system:
        return json.dumps({"decision": "new", "goal_id": None, "rationale": "simulation"}, indent=2)

    if "You are Goal-Setter" in system:
        return json.dumps(
            {"title": "Simulated Goal", "blueprint": "Extract a small, evidence-bound set of key facts."},
            indent=2,
        )

    if "You are a Schema Proposer" in system:
        schema = {
            "fields": [
                {
                    "name": "document_title",
                    "type": "string",
                    "description": "Title or heading of the document (if present).",
                    "evidence_rule": "Quote the exact heading line.",
                },
                {
                    "name": "key_terms",
                    "type": "array[string]",
                    "description": "Up to 5 salient terms that best capture the goal-relevant content.",
                    "evidence_rule": "Each term must appear verbatim in the document.",
                },
            ]
        }
        if "Minimize redundancy" in system:
            schema["fields"] = schema["fields"][:1]
        return json.dumps(schema, indent=2)

    if "You are Prompt-Builder" in system:
        schema = _extract_json_from_text(user) or {}
        field_names = []
        if isinstance(schema, dict):
            fields = schema.get("fields")
            if isinstance(fields, list):
                for f in fields:
                    if isinstance(f, dict) and f.get("name"):
                        field_names.append(str(f["name"]))
        if not field_names:
            field_names = ["field_1"]
        fields_block = "\n".join([f'- "{n}": string | null' for n in field_names])
        return (
            "You are an extractor. Return JSON only.\n\n"
            "Output format:\n"
            "{\n"
            '  "values": { ... },\n'
            '  "evidence": { ... }\n'
            "}\n\n"
            f"Fields:\n{fields_block}\n\n"
            "Evidence rules:\n"
            "- evidence must be an exact quote from the document.\n"
            "- if missing, set value and evidence to null.\n"
        )

    if "You are a Schema Critic" in system:
        return json.dumps(
            {
                "verdict": "revise",
                "strengths": ["Simulation mode: produced a schema with explicit fields."],
                "weaknesses": ["Simulation mode: not grounded in real document content."],
                "suggested_changes": ["Run with a real model to generate document-grounded schemas."],
            },
            indent=2,
        )

    if "You are Governor" in system:
        after = user
        if "CANDIDATES" in user:
            after = user.split("CANDIDATES", 1)[1]
        payload = _extract_json_from_text(after)
        champion = None
        if isinstance(payload, list) and payload:
            first = payload[0]
            if isinstance(first, dict):
                champion = first.get("candidate_id")
        champion = champion or "unknown_candidate"
        return json.dumps(
            {"champion_candidate_id": champion, "rationale": "simulation picks first", "next_improvements": []},
            indent=2,
        )

    if "You are Tutor" in system:
        return "NO-CHANGE"

    if user.startswith("EXHIBIT:"):
        return json.dumps({"values": {"field_1": None}, "evidence": {"field_1": None}}, indent=2)

    return "{}"
