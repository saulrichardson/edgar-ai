# Migration Guide: Edgar-AI v1 to v2

This guide helps you migrate from the original Edgar-AI structure to the new v2 architecture.

## Overview of Changes

### Structural Changes

**Old Structure:**
```
src/edgar_ai/
├── everything mixed together
└── gateway embedded in main module
```

**New Structure:**
```
src/
├── edgar/        # Core configuration
├── gateway/      # Standalone LLM gateway
├── extraction/   # Document processing pipeline
├── storage/      # Data persistence layer
├── interfaces/   # Shared data models
├── cli/          # Command-line interface
└── utils/        # Shared utilities
```

### Key Benefits

1. **Microservices Ready**: Each component can be deployed independently
2. **Clear Boundaries**: Well-defined interfaces between services
3. **Better Testing**: Isolated components are easier to test
4. **Scalability**: Gateway and extraction can scale independently

## Migration Steps

### 1. Update Imports

**Old:**
```python
from edgar_ai.services.goal_setter import GoalSetter
from edgar_ai.interfaces import Document
from edgar_ai.config import settings
```

**New:**
```python
from extraction.services.goal_setter import GoalSetter
from interfaces.models import Document
from edgar.config import settings
```

### 2. Gateway Changes

The gateway is now a standalone service:

**Old:**
```python
# Embedded in main application
from edgar_ai.gateway.server import app
```

**New:**
```python
# Standalone service
from gateway.app.main import app

# Or use the client
from gateway.client import GatewayClient
client = GatewayClient()
```

### 3. Model Updates

All models are now in `interfaces.models`:

**Old:**
```python
from edgar_ai.interfaces import (
    Document, Schema, Row, CriticNote
)
```

**New:**
```python
from interfaces.models import (
    Document, Schema, Row, CriticNote,
    Goal, FieldMeta, ExtractionResult
)
```

### 4. Storage Layer

Storage is now properly abstracted:

**Old:**
```python
# Direct file manipulation
from edgar_ai.memory import Memory
memory = Memory()
```

**New:**
```python
# Abstracted storage
from storage.memory import MemoryStore
from storage.ledger import Ledger
from storage.registry import Registry

memory = MemoryStore()
ledger = Ledger()
registry = Registry()
```

### 5. Configuration

Configuration is centralized in `edgar.config`:

**Old:**
```python
from edgar_ai.config import Settings
settings = Settings()
```

**New:**
```python
from edgar.config import settings  # Pre-instantiated

# Gateway has its own config
from gateway.app.config import settings as gateway_settings
```

## Running the New System

### Development Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Run gateway
edgar-gateway --reload

# Run extraction
edgar-ai extract documents/*.txt

# Or use uvicorn directly
uvicorn gateway.app.main:app --reload
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  gateway:
    build:
      context: .
      dockerfile: Dockerfile.gateway
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
  
  extraction:
    build:
      context: .
      dockerfile: Dockerfile.extraction
    depends_on:
      - gateway
    environment:
      - EDGAR_GATEWAY_URL=http://gateway:8000
```

## API Changes

### Gateway API

The gateway now follows OpenAI's API more closely:

**Old:**
```python
response = await client.complete(prompt="Extract data")
```

**New:**
```python
response = await client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": "Extract data"},
        {"role": "user", "content": document.text}
    ],
    metadata={"persona": "extractor"}
)
```

### Extraction API

The orchestrator is now more modular:

**Old:**
```python
from edgar_ai.orchestrator import run_once
result = run_once(document)
```

**New:**
```python
from extraction.orchestrator import ExtractionPipeline
pipeline = ExtractionPipeline()
result = await pipeline.process(document)
```

## Environment Variables

### Updated Variables

| Old | New | Description |
|-----|-----|-------------|
| `EDGAR_AI_OPENAI_API_KEY` | `OPENAI_API_KEY` | Standard OpenAI key |
| `EDGAR_AI_MODEL` | `EDGAR_EXTRACTOR_MODEL` | Model per persona |
| `LLM_GATEWAY_URL` | `EDGAR_GATEWAY_URL` | Gateway endpoint |

### New Variables

- `EDGAR_GOAL_SETTER_MODEL`: Model for goal setting
- `EDGAR_CRITIC_MODEL`: Model for critique
- `EDGAR_ENABLE_ADVERSARIAL_TESTING`: Enable breaker
- `EDGAR_MEMORY_BACKEND`: Storage backend choice

## Troubleshooting

### Import Errors

If you get import errors, ensure you're using the new package structure:

```bash
# Check PYTHONPATH includes src/
export PYTHONPATH="${PYTHONPATH}:./src"
```

### Gateway Connection

If extraction can't connect to gateway:

```bash
# Check gateway is running
curl http://localhost:8000/health

# Set gateway URL
export EDGAR_GATEWAY_URL=http://localhost:8000
```

### Missing Dependencies

Install all optional dependencies:

```bash
pip install -e ".[dev,storage,aws,monitoring]"
```

## Rollback Plan

If you need to rollback:

1. Keep the old `src/edgar_ai` directory
2. Use git branches for safe migration
3. Test thoroughly before removing old code

```bash
# Create migration branch
git checkout -b migrate-to-v2

# Keep old code available
git checkout main -- src/edgar_ai/
```

## Support

For migration help:
- Check the [architecture documentation](architecture_v2.md)
- Review component READMEs in each directory
- Open an issue with the `migration` label