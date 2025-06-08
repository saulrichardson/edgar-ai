"""Thin HTTP client for the LLM gateway.

Only implements the `/v1/chat/completions` endpoint for now. Retries use
*tenacity* so callers don’t have to sprinkle retry logic everywhere.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings


_BASE_URL = settings.llm_gateway_url


class GatewayUnavailable(RuntimeError):
    """Raised when the gateway URL is not configured."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def chat_completions(model: str, messages: List[Dict[str, str]], **kwargs: Any) -> Dict[str, Any]:
    """Synchronous wrapper around POST /v1/chat/completions."""

    if not _BASE_URL:
        raise GatewayUnavailable("LLM gateway URL not configured in settings")

    url = f"{_BASE_URL.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        **kwargs,
    }

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()
