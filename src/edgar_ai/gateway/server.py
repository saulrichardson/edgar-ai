"""FastAPI application that proxies chat-completions to an underlying LLM.

Today only OpenAI is supported but the implementation is pluggable via an
environment variable ``LLM_PROVIDER``.  The route mirrors the OpenAI HTTP
interface so existing SDK-generated JSON requests work out-of-the-box.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import openai
from fastapi import FastAPI, HTTPException
from fastapi import Request
from starlette.responses import Response
from pydantic import BaseModel, field_validator


class ChatMessage(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def check_role(cls, v: str) -> str:
        if v not in {"system", "user", "assistant", "tool"}:
            raise ValueError("invalid role")
        return v


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: float | None = 0.0
    tools: Any | None = None
    tool_choice: Any | None = None
    max_completion_tokens: int | None = None  # for reasoning models


app = FastAPI(title="LLM Gateway", version="0.1.0", debug=True)


@app.middleware("http")
async def log_llm_traffic(request: Request, call_next):
    """Log chat/completions request & response when recording is enabled."""
    # Only log when flagged by client via header
    if request.url.path != "/v1/chat/completions" or request.headers.get("X-EdgarAI-Record-Session") != "1":
        return await call_next(request)

    from datetime import datetime
    from ..utils.paths import get_data_dir

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    body = await request.body()
    req_dir = get_data_dir() / "llm-traffic" / "requests"
    req_dir.mkdir(parents=True, exist_ok=True)
    (req_dir / f"{timestamp}.json").write_bytes(body)

    # Forward to handler and capture response body
    response = await call_next(request)
    resp_body = b""
    async for chunk in response.body_iterator:
        resp_body += chunk

    resp_dir = get_data_dir() / "llm-traffic" / "responses"
    resp_dir.mkdir(parents=True, exist_ok=True)
    (resp_dir / f"{timestamp}.json").write_bytes(resp_body)

    return Response(content=resp_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)

# Provider selection -----------------------------------------------------


PROVIDER = os.getenv("LLM_PROVIDER", "openai")

if PROVIDER != "openai":  # pragma: no cover
    raise RuntimeError(f"Unsupported LLM_PROVIDER: {PROVIDER}")

# Instantiate once – thread-safe in FastAPI context
# Honour either the standard `OPENAI_API_KEY` or the project-specific
# `EDGAR_AI_OPENAI_API_KEY` environment variable so users following the
# Quick-start guide (which exports the latter) don’t hit authentication
# failures when running through the Gateway.

_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("EDGAR_AI_OPENAI_API_KEY")

_openai_client = openai.OpenAI(api_key=_api_key)


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):  # noqa: D401
    """Normalise the incoming request then proxy to OpenAI."""

    payload = _normalise_request(req)

    try:
        response = _openai_client.chat.completions.create(**payload)
    except openai.OpenAIError as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return response.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Helper: request normalisation
# ---------------------------------------------------------------------------


import re


_REASONING_PATTERN = re.compile(r"^o[0-9]", re.IGNORECASE)


def _normalise_request(req: ChatCompletionRequest) -> Dict[str, Any]:
    """Transform request dict according to model family rules."""

    is_reasoning = bool(_REASONING_PATTERN.match(req.model))

    # Base payload
    payload: Dict[str, Any] = {
        "model": req.model,
        "messages": [m.model_dump() for m in req.messages],
    }

    if is_reasoning:
        # Reasoning models: use max_completion_tokens, no sampling knobs
        payload["max_completion_tokens"] = (
            req.max_completion_tokens if hasattr(req, "max_completion_tokens") else 1024
        )

        # Explicit reasoning_effort default
        payload["reasoning_effort"] = "medium"

        # tool_choice allowed; keep if provided
        if req.tool_choice:
            payload["tool_choice"] = req.tool_choice
        if req.tools:
            payload["tools"] = req.tools

    else:
        # Chat family: keep sampling knobs
        payload.update(
            {
                "temperature": req.temperature or 0.7,
            }
        )
        if req.tools:
            payload["tools"] = req.tools
        if req.tool_choice:
            payload["tool_choice"] = req.tool_choice

    return payload
