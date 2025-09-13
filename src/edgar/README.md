# Edgar Core

This module contains the core configuration and shared utilities for the Edgar-AI system.

## Overview

The `edgar` module serves as the foundation for all other components, providing:

- **Central Configuration**: Environment-based settings management via Pydantic
- **Feature Flags**: Enable/disable advanced features like adversarial testing
- **Model Assignments**: Configure which LLM model each persona uses
- **System Constants**: Shared constants and enums

## Configuration

All configuration is managed through environment variables with sensible defaults:

```bash
# API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Model Selection (per persona)
export EDGAR_GOAL_SETTER_MODEL="gpt-4-turbo-preview"
export EDGAR_EXTRACTOR_MODEL="gpt-4-turbo-preview"
export EDGAR_CRITIC_MODEL="claude-3-opus"

# Feature Flags
export EDGAR_ENABLE_ADVERSARIAL_TESTING=true
export EDGAR_ENABLE_SCHEMA_EVOLUTION=true
```

## Usage

```python
from edgar.config import settings

# Access configuration
print(f"Using {settings.extractor_model} for extraction")

# Feature flag checking
if settings.enable_schema_evolution:
    # Run schema evolution logic
    pass
```

## Design Principles

1. **Zero Config**: The system should work with minimal configuration
2. **Environment-First**: All settings via environment variables for cloud deployment
3. **Type Safety**: Pydantic validation ensures configuration correctness
4. **Feature Flags**: Progressive rollout of new capabilities