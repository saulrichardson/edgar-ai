"""Gateway-specific configuration."""

from pydantic_settings import BaseSettings
from pydantic import Field
import os


class GatewaySettings(BaseSettings):
    """Settings for the Edgar-AI Gateway service."""
    
    # Network settings
    host: str = Field("0.0.0.0", alias="EDGAR_GATEWAY_HOST")
    port: int = Field(8000, alias="EDGAR_GATEWAY_PORT")
    
    # Provider API keys
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(None, alias="ANTHROPIC_API_KEY")
    
    # Retry configuration
    max_retries: int = Field(3, alias="EDGAR_GATEWAY_MAX_RETRIES")
    retry_delay_ms: int = Field(1000, alias="EDGAR_GATEWAY_RETRY_DELAY")
    retry_max_delay_ms: int = Field(60000, alias="EDGAR_GATEWAY_RETRY_MAX_DELAY")
    
    # Logging
    log_level: str = Field("INFO", alias="EDGAR_GATEWAY_LOG_LEVEL")
    record_sessions: bool = Field(False, alias="EDGAR_GATEWAY_RECORD_SESSIONS")
    session_dir: str = Field("data/sessions", alias="EDGAR_GATEWAY_SESSION_DIR")
    
    # Caching
    cache_enabled: bool = Field(True, alias="EDGAR_GATEWAY_CACHE_ENABLED")
    cache_dir: str = Field("data/gateway_cache", alias="EDGAR_GATEWAY_CACHE_DIR")
    
    # Request limits
    max_request_size_mb: int = Field(10, alias="EDGAR_GATEWAY_MAX_REQUEST_SIZE_MB")
    request_timeout_seconds: int = Field(300, alias="EDGAR_GATEWAY_REQUEST_TIMEOUT")
    
    # Feature flags
    enable_streaming: bool = Field(False, alias="EDGAR_GATEWAY_ENABLE_STREAMING")
    enable_fallback_providers: bool = Field(True, alias="EDGAR_GATEWAY_ENABLE_FALLBACK")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = GatewaySettings()

# Backward-compatible environment fallbacks
if not settings.openai_api_key:
    settings.openai_api_key = (
        os.getenv("EDGAR_AI_OPENAI_API_KEY")
        or os.getenv("EDGAR_OPENAI_API_KEY")
        or settings.openai_api_key
    )
