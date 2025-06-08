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


app = FastAPI(title="LLM Gateway", version="0.1.0")

# Provider selection -----------------------------------------------------


PROVIDER = os.getenv("LLM_PROVIDER", "openai")

if PROVIDER != "openai":  # pragma: no cover
    raise RuntimeError(f"Unsupported LLM_PROVIDER: {PROVIDER}")

# Instantiate once – thread-safe in FastAPI context
_openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):  # noqa: D401
    """Proxy chat completion request to the underlying provider."""

    try:
        response = _openai_client.chat.completions.create(
            model=req.model,
            messages=[m.model_dump() for m in req.messages],
            temperature=req.temperature or 0.0,
            tools=req.tools,
            tool_choice=req.tool_choice,
        )
    except openai.OpenAIError as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Convert OpenAI pydantic response to plain dict for JSON serialisation
    return response.model_dump(mode="json")
