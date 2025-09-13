# Edgar-AI Gateway

A unified LLM gateway service that provides provider abstraction, intelligent retry logic, and enterprise features for the Edgar-AI system.

## Overview

The gateway serves as the single point of entry for all LLM interactions in the Edgar-AI system. It abstracts away provider-specific details while adding critical enterprise features like retry logic, request logging, and model routing.

## Features

### Provider Abstraction
- Support for multiple LLM providers (OpenAI, Anthropic, local models)
- Seamless provider switching without code changes
- Fallback chains for high availability

### Intelligent Retry Logic
- Exponential backoff with jitter
- Provider-specific error handling
- Circuit breaker pattern for failing endpoints

### Observability
- Request/response logging for audit trails
- Latency and token usage metrics
- Session recording for debugging

### Model Routing
- Different models for different personas
- Cost optimization through model selection
- A/B testing of model performance

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Gateway   │────▶│  Provider   │
│  (Personas) │     │   (FastAPI) │     │  (OpenAI)   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Middleware  │
                    │  - Retry    │
                    │  - Logging  │
                    │  - Cache    │
                    └─────────────┘
```

## API Endpoints

### Health Check
```
GET /health
```

### Chat Completions
```
POST /v1/chat/completions
{
  "model": "gpt-4-turbo-preview",
  "messages": [...],
  "temperature": 0.0,
  "tools": [...],
  "metadata": {
    "persona": "goal_setter",
    "document_id": "..."
  }
}
```

### Model Listing
```
GET /models
```

## Configuration

```bash
# Gateway network settings
export EDGAR_GATEWAY_HOST=0.0.0.0
export EDGAR_GATEWAY_PORT=8000

# Provider configuration
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Retry configuration
export EDGAR_GATEWAY_MAX_RETRIES=3
export EDGAR_GATEWAY_RETRY_DELAY=1000

# Logging
export EDGAR_GATEWAY_LOG_LEVEL=INFO
export EDGAR_GATEWAY_RECORD_SESSIONS=false
```

## Running the Gateway

### Development
```bash
uvicorn gateway.app.main:app --reload
```

### Production
```bash
gunicorn gateway.app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker
```bash
docker build -f Dockerfile.gateway -t edgar-gateway .
docker run -p 8000:8000 edgar-gateway
```

## Client Usage

```python
from gateway.client import GatewayClient

client = GatewayClient(base_url="http://localhost:8000")

response = await client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": "You are a financial analyst."},
        {"role": "user", "content": "What is the main topic of this 10-K filing?"}
    ],
    metadata={"persona": "goal_setter"}
)
```

## Middleware

### Retry Middleware
Implements exponential backoff with jitter for transient failures:
- 429 (Rate Limit): Wait and retry with backoff
- 503 (Service Unavailable): Immediate retry with jitter
- 500 (Server Error): Retry with exponential backoff

### Logging Middleware
Structured logging for every request:
- Request ID for tracing
- Persona identification
- Token usage and costs
- Latency metrics

### Cache Middleware
Write-through cache for debugging:
- Never serves cached responses
- Stores all requests/responses for analysis
- Configurable retention period

## Security

- API key rotation support
- Rate limiting per client
- Request validation and sanitization
- No storage of sensitive data in logs

## Monitoring

The gateway exposes Prometheus metrics:
- `edgar_gateway_requests_total`
- `edgar_gateway_request_duration_seconds`
- `edgar_gateway_tokens_used_total`
- `edgar_gateway_errors_total`

## Future Enhancements

1. **Streaming Support**: Server-sent events for real-time responses
2. **Request Queuing**: Handle burst traffic gracefully
3. **Cost Optimization**: Automatic model downgrade for simple requests
4. **Multi-Region**: Geographic routing for lowest latency