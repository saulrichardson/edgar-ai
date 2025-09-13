# Edgar-AI Storage Layer

The storage layer provides intelligent data persistence with learning capabilities, enabling the system's continuous improvement through memory and pattern recognition.

## Overview

Beyond simple data storage, this layer is the foundation of Edgar-AI's learning system:

- **Memory**: Learn from past extractions to improve future performance
- **Ledger**: Immutable audit trail of all operations
- **Registry**: Version control for schemas and prompts
- **Ontology**: Build domain knowledge from extracted concepts
- **Raw Lake**: Preserve originals for reprocessing
- **Snapshots**: Debug and compliance capabilities

## Components

### Memory Store
**Purpose**: Enable warm-start extraction and pattern learning

The Memory Store maintains:
- Successful schemas indexed by goal
- Error patterns for common mistakes
- Extraction statistics for optimization
- Field candidate tracking for evolution

```python
from storage.memory import MemoryStore

memory = MemoryStore()

# Store successful schema
await memory.store_schema(schema, goal_id="credit_terms")

# Find matching schema
schema = await memory.find_schema(goal_id="credit_terms")

# Record error pattern
await memory.record_error(
    field="interest_rate",
    error_type="format_mismatch",
    context={"expected": "percentage", "found": "text"}
)
```

### Ledger
**Purpose**: Immutable record of all extractions

Features:
- Cryptographic hashing for integrity
- Full lineage tracking
- Query capabilities for analytics
- Compliance-ready audit trail

```python
from storage.ledger import Ledger

ledger = Ledger()

# Record extraction
entry = await ledger.record(
    document_id="doc123",
    extraction_result=result,
    metadata={"version": "2.0", "model": "gpt-4"}
)

# Query historical extractions
history = await ledger.query(
    document_type="10-K",
    date_range=("2024-01-01", "2024-12-31")
)
```

### Registry
**Purpose**: Version control for schemas and prompts

The Registry enables:
- Schema evolution tracking
- A/B testing of prompts
- Rollback capabilities
- Performance comparison

```python
from storage.registry import Registry

registry = Registry()

# Register new schema version
version = await registry.register_schema(
    schema=new_schema,
    parent_version="v1.2.3",
    changes=["Added debt_covenants field"]
)

# Get schema history
history = await registry.get_schema_history(goal_id="credit_terms")

# Compare versions
diff = await registry.compare_versions("v1.2.3", "v1.2.4")
```

### Ontology
**Purpose**: Build domain knowledge graph

The Ontology:
- Tracks concept relationships
- Identifies synonyms and aliases
- Builds hierarchical taxonomies
- Enables semantic search

```python
from storage.ontology import Ontology

ontology = Ontology()

# Add concept
await ontology.add_concept(
    name="LIBOR",
    category="interest_rate_benchmark",
    aliases=["London Interbank Offered Rate"],
    related_to=["SOFR", "prime_rate"]
)

# Find related concepts
related = await ontology.find_related("LIBOR", max_depth=2)
```

### Raw Lake
**Purpose**: Preserve original documents

Features:
- Compressed storage
- Fast retrieval
- Metadata indexing
- Batch reprocessing support

```python
from storage.raw_lake import RawLake

lake = RawLake()

# Store document
doc_id = await lake.store(
    content=document_html,
    source="SEC EDGAR",
    metadata={"filing_date": "2024-03-15", "form_type": "8-K"}
)

# Retrieve for reprocessing
doc = await lake.retrieve(doc_id)

# Batch retrieval
docs = await lake.retrieve_batch(
    filter={"form_type": "10-K", "year": 2024}
)
```

### Snapshots
**Purpose**: Point-in-time system state capture

Use cases:
- Debugging extraction issues
- Compliance documentation
- Performance analysis
- Reproducibility

```python
from storage.snapshots import SnapshotStore

snapshots = SnapshotStore()

# Create snapshot
snapshot_id = await snapshots.create(
    extraction_id="ext123",
    state={
        "prompt": prompt_text,
        "model_response": response,
        "extracted_data": rows,
        "critic_feedback": notes
    }
)

# Restore for debugging
state = await snapshots.restore(snapshot_id)
```

## Storage Backends

### Filesystem (Development)
- Simple file-based storage
- JSON and Parquet formats
- Easy debugging and inspection

### PostgreSQL (Production)
- ACID compliance
- Advanced querying
- Concurrent access
- Backup/restore

### S3 + DynamoDB (Scale)
- Unlimited storage
- Global distribution
- Cost-effective
- Serverless-ready

## Configuration

```python
# In edgar/config.py
EDGAR_MEMORY_BACKEND = "postgresql"  # filesystem, postgresql, dynamodb
EDGAR_STORAGE_CONNECTION = "postgresql://user:pass@host/db"
EDGAR_RAW_LAKE_BUCKET = "s3://edgar-raw-documents"
EDGAR_SNAPSHOT_RETENTION_DAYS = 90
```

## Data Retention

### Retention Policies

| Data Type | Default Retention | Configurable |
|-----------|------------------|--------------|
| Raw Documents | Indefinite | Yes |
| Extracted Data | Indefinite | Yes |
| Schemas | Indefinite | No |
| Error Logs | 1 year | Yes |
| Snapshots | 90 days | Yes |
| Metrics | 1 year | Yes |

### GDPR Compliance

- Right to erasure support
- Data anonymization tools
- Audit trail preservation
- Consent tracking

## Performance Optimization

### Caching Strategy
- In-memory cache for hot schemas
- Redis for distributed caching
- TTL-based invalidation
- Lazy loading

### Query Optimization
- Indexed fields for common queries
- Materialized views for analytics
- Partition by date/document type
- Connection pooling

## Monitoring

Key metrics:
- Storage growth rate
- Query performance (p50, p95, p99)
- Cache hit rates
- Schema version distribution
- Error pattern frequency

## Backup and Recovery

### Backup Strategy
- Daily full backups
- Continuous incremental backups
- Cross-region replication
- Point-in-time recovery

### Disaster Recovery
- RTO: 4 hours
- RPO: 1 hour
- Automated failover
- Regular DR testing

## Best Practices

1. **Use appropriate backend**: Filesystem for dev, PostgreSQL for prod
2. **Monitor storage growth**: Set up alerts for unusual patterns
3. **Regular cleanup**: Archive old snapshots and logs
4. **Test backups**: Regularly verify backup integrity
5. **Version everything**: Never modify schemas in place

## Future Enhancements

1. **Graph Database Integration**: Neo4j for complex ontologies
2. **Time-Series Storage**: Optimized for temporal patterns
3. **Federated Queries**: Query across multiple deployments
4. **ML Model Storage**: Version control for fine-tuned models