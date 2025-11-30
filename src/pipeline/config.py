from __future__ import annotations

import os
from dataclasses import dataclass

from clients.gateway import GatewayConfig


def _getenv(name: str, default: str) -> str:
    return os.getenv(name, default)


def load_gateway_config() -> GatewayConfig:
    return GatewayConfig(
        url=_getenv("GATEWAY_URL", "http://127.0.0.1:8000/v1/responses"),
        model=_getenv("MODEL", "openai:gpt-5"),
        reasoning_effort=_getenv("REASONING_EFFORT", "medium"),
        timeout_seconds=float(_getenv("GATEWAY_TIMEOUT_SECONDS", "180")),
    )
