# Edgar-AI Interfaces

Shared data models and interfaces that ensure consistency and type safety across all Edgar-AI services.

## Overview

The interfaces module provides:
- **Pydantic Models**: Type-safe data validation
- **Clear Contracts**: Well-defined interfaces between services
- **API Documentation**: Auto-generated from models
- **Schema Evolution**: Support for backward-compatible changes

## Core Models

### Document Models

```python
from interfaces.models import Document, DocumentMetadata

# Input document
document = Document(
    id="edgar_8k_20240315",
    text="CREDIT AGREEMENT dated as of March 15, 2024...",
    metadata=DocumentMetadata(
        source="SEC EDGAR",
        form_type="8-K",
        filing_date="2024-03-15",
        company="Example Corp",
        cik="0001234567"
    )
)
```

### Goal Models

```python
from interfaces.models import Goal, FieldCandidate

# Extraction goal
goal = Goal(
    goal_id="extract_credit_terms",
    overview="Extract key terms from credit agreement",
    topics=["loan amount", "interest rate", "maturity"],
    fields=[
        FieldCandidate(
            name="principal_amount",
            type="currency",
            description="Total loan principal"
        )
    ]
)
```

### Schema Models

```python
from interfaces.models import Schema, FieldMeta

# Extraction schema
schema = Schema(
    id="credit_terms_v1",
    goal_id="extract_credit_terms",
    name="Credit Agreement Terms",
    description="Key terms from credit facility agreements",
    fields=[
        FieldMeta(
            name="principal_amount",
            type="currency",
            description="Total loan principal amount",
            required=True,
            examples=["$100,000,000", "$50M"]
        )
    ]
)
```

### Extraction Models

```python
from interfaces.models import Row, ExtractionResult

# Extracted data
row = Row(
    schema_id="credit_terms_v1",
    data={
        "principal_amount": 100000000,
        "interest_rate": 0.045,
        "maturity_date": "2029-03-15"
    },
    metadata={
        "confidence": 0.95,
        "source_page": 12
    }
)

# Complete result
result = ExtractionResult(
    document_id="edgar_8k_20240315",
    goal=goal,
    schema=schema,
    rows=[row],
    critic_notes=[],
    decision=GovernorDecision(
        status="approved",
        quality_score=0.95
    )
)
```

### Feedback Models

```python
from interfaces.models import CriticNote, Improvement

# Critic feedback
note = CriticNote(
    row_index=0,
    field_name="interest_rate",
    score=0.7,
    feedback="Format inconsistent - found percentage as text",
    suggestion="Enforce numeric extraction for percentage fields",
    severity="warning"
)

# Improvement suggestion
improvement = Improvement(
    schema_id="credit_terms_v1",
    description="Improve interest rate extraction",
    changes=[
        "Add explicit percentage parsing",
        "Handle basis points notation"
    ],
    expected_impact="Reduce format errors by 80%"
)
```

## Model Validation

All models include built-in validation:

```python
from interfaces.models import Schema
from pydantic import ValidationError

try:
    # Invalid schema - missing required fields
    schema = Schema(
        id="test",
        fields=[]  # Error: need goal_id, name, description
    )
except ValidationError as e:
    print(e.errors())
```

## Type System

### Field Types

| Type | Description | Example |
|------|-------------|---------|
| `text` | Plain text | "Example Corp" |
| `number` | Numeric value | 123.45 |
| `currency` | Monetary amount | 1000000 |
| `percentage` | Percentage value | 0.045 |
| `date` | ISO date | "2024-03-15" |
| `boolean` | True/False | true |
| `array` | List of values | ["A", "B", "C"] |
| `object` | Nested structure | {"key": "value"} |

### Custom Types

```python
from typing import Literal
from pydantic import BaseModel

class CustomFieldType(BaseModel):
    type: Literal["interest_rate_basis"]
    unit: Literal["percentage", "basis_points", "spread"]
    base_rate: Optional[str] = None
```

## API Integration

Models automatically generate OpenAPI schemas:

```python
from fastapi import FastAPI
from interfaces.models import Document, ExtractionResult

app = FastAPI()

@app.post("/extract", response_model=ExtractionResult)
async def extract_document(document: Document):
    # Process document
    pass
```

## Serialization

Models support multiple serialization formats:

```python
# JSON serialization
json_str = schema.model_dump_json(indent=2)

# Dictionary conversion
data_dict = schema.model_dump(exclude_unset=True)

# Validation from JSON
schema = Schema.model_validate_json(json_str)
```

## Evolution Support

Models support schema evolution:

```python
from interfaces.models import SchemaVersion

# Track schema versions
version = SchemaVersion(
    version="2.0.0",
    changes=[
        "Added 'loan_purpose' field",
        "Made 'collateral' field optional"
    ],
    backward_compatible=True,
    migration_script="migrations/v2_0_0.py"
)
```

## Best Practices

1. **Use Type Hints**: Always specify types for clarity
2. **Validate Early**: Validate at service boundaries
3. **Version Models**: Track model changes explicitly
4. **Document Fields**: Use descriptions for all fields
5. **Provide Examples**: Include examples in field metadata

## Testing

Models include test fixtures:

```python
from interfaces.fixtures import (
    sample_document,
    sample_schema,
    sample_extraction_result
)

def test_extraction():
    doc = sample_document()
    assert doc.id == "test_doc_001"
```

## Future Enhancements

1. **GraphQL Support**: Auto-generate GraphQL schemas
2. **Protocol Buffers**: Binary serialization for performance
3. **JSON Schema Export**: Generate standalone schemas
4. **Type Migrations**: Automated type evolution