"""Central configuration using *pydantic-settings*.

The project requires this dependency.  For offline unit-test environments a
small stub is vendored under ``edgar_ai._vendor.pydantic_settings`` so imports
always succeed, but production installs SHOULD add the real package to ensure
full behaviour (env-var parsing, .env loading, etc.).
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Ensure *pydantic_settings* import is available either from the real package
# or from the internal vendor shim.
# ---------------------------------------------------------------------------


try:
    import pydantic_settings  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    # Insert vendored shim into sys.modules so subsequent imports work.
    from edgar_ai._vendor import pydantic_settings as _shim

    sys.modules["pydantic_settings"] = _shim  # type: ignore


# Now import the (real or shimmed) objects.

from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore  # noqa: E402


class Settings(BaseSettings):
    """Project-wide settings loaded from environment or .env file."""

    openai_api_key: Optional[str] = None
    batch_size: int = 8
    database_uri: str = "sqlite:///:memory:"
    llm_gateway_url: Optional[str] = None
    # Model selections per persona (overridable via .env)
    model_goal_setter: str = "o4-mini"
    # Goal-Setter LLM temperature (applicable when calling the gateway)
    goal_setter_temperature: float = 0.3
    # Goal-Setter JSON parse retry attempts (configurable via env var)
    goal_setter_max_retries: int = 3
    model_extractor: str = "gpt-4.1"
    model_critic: str = "o4-mini"
    simulate: bool = False  # offline / deterministic mode

    model_config = SettingsConfigDict(
        env_prefix="EDGAR_AI_",
        env_file=".env",
        protected_namespaces=(),
    )


# Singleton used across the codebase
settings = Settings()  # type: ignore[var-annotated]


def is_configured() -> bool:  # noqa: D401
    """Return ``True`` if the mandatory OpenAI key is present."""

    return settings.openai_api_key is not None
