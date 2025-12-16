from __future__ import annotations

import os
from dataclasses import dataclass

from clients.gateway import GatewayConfig


def _getenv(name: str, default: str) -> str:
    return os.getenv(name, default)


def load_gateway_config() -> GatewayConfig:
    host = _getenv("GATEWAY_HOST", "127.0.0.1")
    port = _getenv("GATEWAY_PORT", "8000")
    default_url = f"http://{host}:{port}/v1/responses"
    return GatewayConfig(
        url=_getenv("GATEWAY_URL", default_url),
        model=_getenv("MODEL", "openai:gpt-5"),
        reasoning_effort=_getenv("REASONING_EFFORT", "medium"),
        timeout_seconds=float(_getenv("GATEWAY_TIMEOUT_SECONDS", "180")),
    )
