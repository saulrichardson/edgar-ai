"""Memory store for schema reuse and learning."""

from typing import Optional, List, Dict
import json
from pathlib import Path
from datetime import datetime

from interfaces.models import Schema, ErrorRecord, Improvement
from edgar.config import settings


class MemoryStore:
    """
    Persistent memory for schemas, errors, and improvements.
    
    Enables:
    - Warm-start extraction through schema reuse
    - Error pattern learning
    - Improvement tracking
    - Performance optimization
    """
    
    def __init__(self):
        self.backend = settings.memory_backend
        self.base_path = Path(settings.data_dir) / "memory"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for performance
        self._schema_cache: Dict[str, Schema] = {}
        self._error_patterns: List[ErrorRecord] = []
    
    async def store_schema(
        self, 
        schema: Schema, 
        parent_id: Optional[str] = None
    ) -> str:
        """
        Store a schema with optional lineage.
        
        Args:
            schema: Schema to store
            parent_id: Parent schema ID if this is an evolution
            
        Returns:
            Schema ID
        """
        # Store in filesystem (stub for other backends)
        schema_path = self.base_path / "schemas" / f"{schema.id}.json"
        schema_path.parent.mkdir(exist_ok=True)
        
        schema_data = schema.model_dump()
        schema_data["parent_id"] = parent_id
        schema_data["created_at"] = datetime.utcnow().isoformat()
        
        with open(schema_path, "w") as f:
            json.dump(schema_data, f, indent=2)
        
        # Update cache
        self._schema_cache[schema.goal_id] = schema
        
        return schema.id
    
    async def find_schema(self, goal_id: str) -> Optional[Schema]:
        """
        Find a schema by goal ID.
        
        Args:
            goal_id: Goal identifier
            
        Returns:
            Matching schema or None
        """
        # Check cache first
        if goal_id in self._schema_cache:
            return self._schema_cache[goal_id]
        
        # Search filesystem
        schema_dir = self.base_path / "schemas"
        if not schema_dir.exists():
            return None
        
        for schema_file in schema_dir.glob("*.json"):
            with open(schema_file) as f:
                data = json.load(f)
                if data.get("goal_id") == goal_id:
                    schema = Schema.model_validate(data)
                    self._schema_cache[goal_id] = schema
                    return schema
        
        return None
    
    async def list_schemas(self) -> List[Schema]:
        """List all available schemas."""
        schemas = []
        schema_dir = self.base_path / "schemas"
        
        if schema_dir.exists():
            for schema_file in schema_dir.glob("*.json"):
                with open(schema_file) as f:
                    data = json.load(f)
                    schemas.append(Schema.model_validate(data))
        
        return schemas
    
    async def record_error(
        self,
        field: str,
        error_type: str,
        context: dict
    ) -> None:
        """
        Record an error pattern for learning.
        
        Args:
            field: Field that had the error
            error_type: Type of error
            context: Additional context
        """
        error = ErrorRecord(
            field=field,
            error_type=error_type,
            context=context,
            timestamp=datetime.utcnow()
        )
        
        self._error_patterns.append(error)
        
        # Persist to disk
        error_file = self.base_path / "errors" / f"{datetime.utcnow().date()}.jsonl"
        error_file.parent.mkdir(exist_ok=True)
        
        with open(error_file, "a") as f:
            f.write(error.model_dump_json() + "\n")
    
    async def get_error_patterns(
        self, 
        field: Optional[str] = None
    ) -> List[ErrorRecord]:
        """
        Get error patterns, optionally filtered by field.
        
        Args:
            field: Optional field filter
            
        Returns:
            List of error records
        """
        if field:
            return [e for e in self._error_patterns if e.field == field]
        return self._error_patterns
    
    async def queue_improvements(
        self, 
        improvements: List[Improvement]
    ) -> None:
        """Queue improvements for testing."""
        queue_file = self.base_path / "improvements" / "queue.jsonl"
        queue_file.parent.mkdir(exist_ok=True)
        
        with open(queue_file, "a") as f:
            for improvement in improvements:
                f.write(improvement.model_dump_json() + "\n")
    
    async def record_extraction(
        self,
        document_id: str,
        goal_id: str,
        schema_id: str,
        rows: List,
        critic_notes: List,
        decision: dict
    ) -> None:
        """Record extraction results for analytics."""
        record = {
            "document_id": document_id,
            "goal_id": goal_id,
            "schema_id": schema_id,
            "row_count": len(rows),
            "critic_score": self._calculate_score(critic_notes),
            "decision": decision.status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store extraction record
        record_file = self.base_path / "extractions" / f"{datetime.utcnow().date()}.jsonl"
        record_file.parent.mkdir(exist_ok=True)
        
        with open(record_file, "a") as f:
            f.write(json.dumps(record) + "\n")
    
    def _calculate_score(self, critic_notes: List) -> float:
        """Calculate average critic score."""
        if not critic_notes:
            return 1.0
        
        scores = [note.score for note in critic_notes if note.score is not None]
        return sum(scores) / len(scores) if scores else 0.5