"""Central configuration using *pydantic-settings*.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Pydantic-settings configuration
# ---------------------------------------------------------------------------
# The real *pydantic-settings* package is now declared as a hard dependency
# in pyproject.toml, so the previous fallback to an internal vendored stub is
# no longer required.  We simply import the objects directly and allow the
# usual Python import-error to propagate if the package is missing.
# ---------------------------------------------------------------------------


from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


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
