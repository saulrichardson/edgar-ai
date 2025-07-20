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
    # Goal-Setter / Variant-Generator LLM temperature
    goal_setter_temperature: float = 0.8
    # Goal-Setter JSON parse retry attempts (configurable via env var)
    goal_setter_max_retries: int = 3
    model_extractor: str = "gpt-4.1"
    model_critic: str = "o4-mini"
    # Prompt-Builder LLM model & temperature for dynamic prompt engineering
    model_prompt_builder: str = "o4-mini"
    prompt_builder_temperature: float = 0.3

    # ---------------------------------------------------------------------
    # Phase-4 additions
    # ---------------------------------------------------------------------
    # Upper bound on the number of tokens Prompt-Builder is allowed to
    # generate when crafting the extraction prompt.  The builder should trim
    # or otherwise compact the text to remain within this budget.  We expose
    # it as a setting so experiments can tune the prompt length without code
    # changes.
    prompt_builder_max_tokens: int = 4096

    # The Extractor may retry transient gateway/validation failures.  This is
    # the maximum number of attempts before raising.  By default we keep it
    # very small as most failures are deterministic model errors.  Increase
    # in production deployments if gateway connectivity is flaky.
    extractor_max_retries: int = 3

    # Toggle to disable the Extractor validation layer altogether (for
    # debugging or rapid experimentation).  When *False* the extractor will
    # accept whatever JSON the LLM returns and map it into a Row object
    # without checks.
    extractor_validation: bool = True

    # Discoverer / Schema-Synth
    model_discoverer: str = "o4-mini"
    model_schema_synth: str = "o4-mini"
    discoverer_temperature: float = 0.3
    schema_synth_temperature: float = 0.3
    simulate: bool = False  # offline / deterministic mode

    # Schema-Critic LLM model & high-level design principles for schema review
    model_schema_critic: str = "o4-mini"
    schema_critic_principles: list[str] = [
        "completeness (covers all necessary fields without omissions)",
        "orthogonality (fields are non-overlapping and independent)",
        "conciseness (no redundant or overly verbose fields)",
        "consistency with exhibit structure (logical grouping)",
        "robustness to missing data (graceful degradation)",
    ]

    # HTTP timeout (seconds) for calls to the LLM gateway – default 5 minutes
    gateway_timeout: int = 300

    # Toggle to inject additional guiding principles into Goal-Setter prompts
    extra_principles: bool = True  # EDGAR_AI_EXTRA_PRINCIPLES

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
