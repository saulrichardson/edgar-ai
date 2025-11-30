"""Thin sync client for the local gateway /v1/responses endpoint.

Designed for deterministic persona pipelines: always streams, accumulates text output.
"""
from __future__ import annotations

import json
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
    for evt in events:
        t = evt.get("type")
        if t == "response.output_text.delta":
            parts.append(evt.get("delta", ""))
        elif t == "response.output_text.done":
            parts.append(evt.get("text", ""))
    return "".join(parts).strip()


def send_chat(
    messages: List[Dict[str, str]],
    config: GatewayConfig,
    *,
    stream: bool = True,
) -> str:
    """Send chat messages to the gateway and return concatenated output text.

    The gateway only supports streaming. We parse SSE-style data lines and collect text deltas.
    """
    payload: Dict[str, Any] = {
        "model": config.model,
        "reasoning": {"effort": config.reasoning_effort},
        "stream": stream,
        "input": messages,
    }

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
            if line.startswith(b"data: "):
                try:
                    evt = json.loads(line[len("data: ") :])
                except json.JSONDecodeError:
                    continue
                events.append(evt)
    return _extract_output_text(events)
