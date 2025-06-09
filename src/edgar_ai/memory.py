"""In-memory storage for schema records with rationales."""

from abc import ABC, abstractmethod
from typing import List

from pydantic import BaseModel


class SchemaRecord(BaseModel):
    """A record of a generated schema and its rationale."""

    schema_id: str
    schema: dict
    rationale: str


class MemoryStore(ABC):
    """Abstract interface for storing and retrieving schema records."""

    @abstractmethod
    def save_schema_record(self, schema_id: str, schema: dict, rationale: str) -> None:
        """Persist a new schema record."""
        ...

    @abstractmethod
    def list_schema_records(self) -> List[SchemaRecord]:
        """Return all previously saved schema records."""
        ...


class InMemoryStore(MemoryStore):
    """In-memory implementation of MemoryStore (for testing and prototyping)."""

    def __init__(self) -> None:
        self._records: List[SchemaRecord] = []

    def save_schema_record(self, schema_id: str, schema: dict, rationale: str) -> None:
        record = SchemaRecord(schema_id=schema_id, schema=schema, rationale=rationale)
        self._records.append(record)

    def list_schema_records(self) -> List[SchemaRecord]:
        return list(self._records)