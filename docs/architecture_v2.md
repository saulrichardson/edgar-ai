# Edgar-AI Architecture v2: AI-First Document Intelligence

## Overview

Edgar-AI v2 represents a complete architectural redesign that puts AI at the center of financial document processing. This system transforms SEC EDGAR filings into structured, queryable data through an ensemble of specialized AI personas, each contributing to a self-improving data extraction pipeline.

## Core Philosophy

### 1. **AI-Native Design**
Every component is designed to leverage LLM capabilities:
- Goal determination through AI reasoning, not hard-coded rules
- Schema evolution via AI critique and refinement
- Self-healing extraction through continuous learning
- Adversarial testing with AI-generated edge cases

### 2. **Microservices-Ready Architecture**
Clean separation of concerns enables:
- Independent scaling of gateway vs extraction services
- Provider-agnostic LLM integration
- Distributed processing of large document batches
- Zero-downtime updates to individual components

### 3. **Continuous Learning Loop**
The system improves automatically through:
- Critic feedback on extraction quality
- Tutor-generated prompt improvements
- Champion-challenger testing
- Back-correction of historical data

## Architecture Components

### 1. Gateway Layer (`/src/gateway/`)
**Purpose**: Unified LLM interface with provider abstraction

The gateway provides a standardized API for all LLM interactions, abstracting away provider-specific details and adding enterprise features:

- **Provider Abstraction**: Swap between OpenAI, Anthropic, or custom models without code changes
- **Intelligent Retry Logic**: Exponential backoff with jitter for transient failures
- **Request/Response Logging**: Full audit trail for compliance and debugging
- **Model Routing**: Different personas can use different models based on task requirements
- **Token Optimization**: Automatic context window management and prompt compression

**Key Innovation**: Recording mode captures entire LLM sessions for replay testing and debugging.

### 2. Extraction Pipeline (`/src/extraction/`)
**Purpose**: Orchestrate the document processing flow

The extraction pipeline implements the data fly-wheel pattern:

```
Document → Goal Setting → Schema Selection/Evolution → 
Prompt Building → Extraction → Critique → Learning
```

**Services**:
- **Goal Setter**: Determines what information to extract based on document content
- **Schema Evolution Engine**: Creates and refines extraction schemas
- **Prompt Builder**: Converts schemas to optimized extraction prompts
- **Extractor**: Performs structured data extraction via function calling
- **Critic**: Evaluates extraction quality and provides feedback
- **Tutor**: Generates improved prompts based on critic feedback
- **Governor**: Enforces quality gates and manages promotion logic
- **Breaker**: Creates adversarial test cases to strengthen the system

### 3. Storage Layer (`/src/storage/`)
**Purpose**: Intelligent data persistence with learning capabilities

Beyond simple data storage, this layer enables the system's learning capabilities:

- **Memory**: Stores successful schemas and extraction patterns for reuse
- **Ledger**: Immutable record of all extracted data with full lineage
- **Registry**: Version control for schemas with champion-challenger tracking
- **Ontology**: Domain knowledge graph built from extracted concepts
- **Raw Lake**: Original documents for back-correction and reprocessing
- **Snapshots**: Point-in-time captures for debugging and compliance

### 4. Interfaces (`/src/interfaces/`)
**Purpose**: Shared data models ensuring consistency across services

Clean, Pydantic-based models that:
- Enforce data validation at boundaries
- Enable automatic API documentation
- Support schema evolution without breaking changes
- Provide clear contracts between services

### 5. CLI (`/src/cli/`)
**Purpose**: Developer-friendly command-line interface

Enables:
- Batch processing of document collections
- Interactive debugging sessions
- Performance benchmarking
- Schema management operations

## AI-First Innovations

### 1. Goal-Driven Extraction
Instead of pre-defining extraction templates, the system asks: "What's the most valuable information in this document?" This enables:
- Automatic adaptation to new document types
- Discovery of previously unknown data patterns
- Focus on high-value information extraction

### 2. Schema as Living Entities
Schemas evolve through:
- **Promotion**: Frequently seen patterns become first-class schema fields
- **Deprecation**: Unused fields are automatically removed
- **Refinement**: Field definitions improve based on extraction feedback
- **Forking**: Specialized schemas emerge for document subtypes

### 3. Adversarial Hardening
The Breaker service continuously:
- Generates synthetic documents designed to fail current extractors
- Tests edge cases before they appear in production
- Forces continuous improvement of extraction logic

### 4. Multi-Persona Collaboration
Different AI personas excel at different tasks:
- **Analyst** (Goal Setter): Business understanding
- **Architect** (Schema Designer): Data modeling
- **Worker** (Extractor): Precise execution
- **Auditor** (Critic): Quality assurance
- **Teacher** (Tutor): Continuous improvement

## Deployment Patterns

### 1. Monolithic Development
```
docker-compose up  # Runs all services locally
```

### 2. Distributed Production
```yaml
# Kubernetes deployment
- Gateway: 3 replicas with load balancing
- Extraction Workers: Auto-scaling based on queue depth
- Storage: Managed cloud services (S3, PostgreSQL)
```

### 3. Serverless Extraction
- Lambda functions for document processing
- Step Functions for orchestration
- DynamoDB for schema storage

## Performance Optimizations

### 1. Warm-Start Extraction
- Previously successful schemas skip evolution phase
- 10x faster processing for known document types
- Automatic fallback to cold-start if confidence drops

### 2. Batched Processing
- Multiple documents processed in parallel
- Shared context for similar documents
- Efficient token usage through prompt batching

### 3. Incremental Learning
- Online learning without full retraining
- Immediate application of improvements
- No downtime for model updates

## Security & Compliance

### 1. Data Isolation
- Tenant separation at storage layer
- No cross-contamination of extracted data
- Audit logs for all operations

### 2. Model Security
- Local deployment option for sensitive data
- API key rotation and management
- Rate limiting and abuse prevention

### 3. Compliance Features
- Full data lineage tracking
- Explanation generation for extractions
- GDPR-compliant data deletion

## Future Directions

### 1. Multi-Modal Processing
- Integration with document layout understanding
- Table and chart extraction
- Handwritten note processing

### 2. Real-Time Streaming
- WebSocket support for live document feeds
- Incremental extraction as documents arrive
- Event-driven architecture

### 3. Federated Learning
- Learn from multiple deployments without data sharing
- Industry-wide pattern recognition
- Privacy-preserving improvements

## Getting Started

See the [quickstart guide](quickstart.md) for installation and basic usage. For detailed component documentation, refer to the README files in each module directory.