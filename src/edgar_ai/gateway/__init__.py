"""Lightweight LLM gateway micro-service.

This sub-package provides both the FastAPI application (server) and a minimal
Python client used by services inside *edgar_ai*.  The gateway exposes an
endpoint compatible with OpenAI’s chat-completion schema so that downstream
code can stay unchanged when switching providers.
"""

from __future__ import annotations

# Re-export the FastAPI app so external processes can do
# `uvicorn edgar_ai.gateway:app`.

from .server import app  # noqa: F401
