"""Main FastAPI application for the Edgar-AI Gateway."""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .middleware.logging import LoggingMiddleware
from .middleware.retry import RetryMiddleware
from .providers.base import LLMProvider
from .providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

# Global provider registry
providers: Dict[str, LLMProvider] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting Edgar-AI Gateway")
    
    # Initialize providers
    if settings.openai_api_key:
        providers["openai"] = OpenAIProvider(api_key=settings.openai_api_key)
        logger.info("OpenAI provider initialized")
    
    if not providers:
        logger.error("No LLM providers configured")
        raise RuntimeError("At least one LLM provider must be configured")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Edgar-AI Gateway")
    for provider in providers.values():
        await provider.close()


app = FastAPI(
    title="Edgar-AI Gateway",
    description="Unified LLM gateway for the Edgar-AI document intelligence system",
    version="2.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RetryMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "providers": list(providers.keys()),
        "version": "2.0.0",
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, body: Dict[str, Any]):
    """
    OpenAI-compatible chat completions endpoint.
    
    Supports additional metadata for persona identification and request tracking.
    """
    # Extract provider from model name or metadata
    model = body.get("model", "gpt-4-turbo-preview")
    metadata = body.get("metadata", {})
    persona = metadata.get("persona", "unknown")
    
    # For now, route all requests to OpenAI
    provider = providers.get("openai")
    if not provider:
        raise HTTPException(status_code=503, detail="OpenAI provider not available")
    
    # Log the request
    logger.info(f"Chat completion request from persona: {persona}, model: {model}")
    
    try:
        # Forward to provider
        response = await provider.chat_completion(body)
        return response
    except Exception as e:
        logger.error(f"Provider error: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/models")
async def list_models():
    """List available models across all providers."""
    models = []
    
    for provider_name, provider in providers.items():
        provider_models = await provider.list_models()
        for model in provider_models:
            models.append({
                "id": model,
                "provider": provider_name,
                "personas": _get_recommended_personas(model),
            })
    
    return {"models": models}


def _get_recommended_personas(model: str) -> list[str]:
    """Get recommended personas for a given model."""
    if "gpt-4" in model or "claude-3-opus" in model:
        return ["goal_setter", "schema_designer", "critic", "tutor"]
    elif "gpt-3.5" in model or "claude-3-sonnet" in model:
        return ["extractor"]
    else:
        return ["all"]


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    # Stub for metrics - would integrate with prometheus_client in production
    return {
        "edgar_gateway_requests_total": 0,
        "edgar_gateway_errors_total": 0,
        "edgar_gateway_tokens_used_total": 0,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)