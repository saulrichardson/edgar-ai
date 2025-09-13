"""Central configuration for Edgar-AI system."""

from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    """Global settings for Edgar-AI."""
    
    # API Keys
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(None, alias="ANTHROPIC_API_KEY")
    
    # Gateway settings
    gateway_url: str = Field("http://localhost:8000", alias="EDGAR_GATEWAY_URL")
    gateway_timeout: int = Field(300, alias="EDGAR_GATEWAY_TIMEOUT")
    
    # Model assignments per persona
    goal_setter_model: str = Field("gpt-4-turbo-preview", alias="EDGAR_GOAL_SETTER_MODEL")
    schema_designer_model: str = Field("gpt-4-turbo-preview", alias="EDGAR_SCHEMA_DESIGNER_MODEL")
    extractor_model: str = Field("gpt-4-turbo-preview", alias="EDGAR_EXTRACTOR_MODEL")
    critic_model: str = Field("gpt-4-turbo-preview", alias="EDGAR_CRITIC_MODEL")
    tutor_model: str = Field("gpt-4-turbo-preview", alias="EDGAR_TUTOR_MODEL")
    
    # Extraction settings
    max_extraction_retries: int = Field(3, alias="EDGAR_MAX_EXTRACTION_RETRIES")
    extraction_temperature: float = Field(0.0, alias="EDGAR_EXTRACTION_TEMPERATURE")
    
    # Learning settings
    schema_promotion_threshold: int = Field(10, alias="EDGAR_SCHEMA_PROMOTION_THRESHOLD")
    champion_challenger_min_samples: int = Field(100, alias="EDGAR_CHAMPION_CHALLENGER_MIN_SAMPLES")
    
    # Storage settings
    data_dir: str = Field("data", alias="EDGAR_DATA_DIR")
    memory_backend: str = Field("filesystem", alias="EDGAR_MEMORY_BACKEND")
    
    # Feature flags
    enable_adversarial_testing: bool = Field(False, alias="EDGAR_ENABLE_ADVERSARIAL_TESTING")
    enable_back_correction: bool = Field(False, alias="EDGAR_ENABLE_BACK_CORRECTION")
    enable_schema_evolution: bool = Field(True, alias="EDGAR_ENABLE_SCHEMA_EVOLUTION")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()

# Backward-compatible environment fallbacks for common env var names
if not settings.openai_api_key:
    settings.openai_api_key = (
        os.getenv("EDGAR_AI_OPENAI_API_KEY")
        or os.getenv("EDGAR_OPENAI_API_KEY")
        or settings.openai_api_key
    )

# Allow alternate gateway URL env var name used in some setups
alt_gateway_url = os.getenv("EDGAR_AI_LLM_GATEWAY_URL")
if alt_gateway_url:
    settings.gateway_url = alt_gateway_url
