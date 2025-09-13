"""Schema Evolution Engine for creating and refining extraction schemas."""

from typing import List, Optional

from interfaces.models import Document, Schema, FieldCandidate
from storage.memory import MemoryStore
from gateway.client import GatewayClient
from edgar.config import settings


class SchemaEvolution:
    """
    Creates and evolves extraction schemas based on document patterns.
    
    This service handles:
    - Creating new schemas for unseen document types
    - Evolving existing schemas based on usage patterns
    - Promoting frequently seen field candidates
    - Managing schema versions and lineage
    """
    
    def __init__(self):
        self.client = GatewayClient()
        self.memory = MemoryStore()
        self.model = settings.schema_designer_model
    
    async def create_schema(self, goal_id: str, document: Document) -> Schema:
        """
        Create a new schema for a goal.
        
        This involves:
        1. Generating multiple schema candidates
        2. Evaluating each against design principles
        3. Selecting the best candidate
        4. Storing for future use
        """
        # Generate candidates
        candidates = await self._generate_candidates(goal_id, document)
        
        # Evaluate candidates
        evaluations = await self._evaluate_candidates(candidates, document)
        
        # Select winner
        winner = self._select_winner(candidates, evaluations)
        
        # Store in memory
        await self.memory.store_schema(winner)
        
        return winner
    
    async def evolve_schema(
        self, 
        schema: Schema, 
        field_candidates: List[FieldCandidate]
    ) -> Optional[Schema]:
        """
        Evolve an existing schema based on field candidates.
        
        Args:
            schema: Current schema
            field_candidates: New fields discovered in documents
            
        Returns:
            New schema version if evolution warranted, None otherwise
        """
        # Check promotion threshold
        promotable = [
            fc for fc in field_candidates 
            if fc.occurrence_count >= settings.schema_promotion_threshold
        ]
        
        if not promotable:
            return None
        
        # Create new schema version
        new_schema = await self._create_evolved_schema(schema, promotable)
        
        # Store with lineage
        await self.memory.store_schema(new_schema, parent_id=schema.id)
        
        return new_schema
    
    async def list_schemas(self) -> List[Schema]:
        """List all available schemas."""
        return await self.memory.list_schemas()
    
    async def promote_field(self, field_name: str, goal_id: str):
        """Manually promote a field candidate to a schema."""
        # Stub implementation
        pass
    
    async def backfill_with_new_schema(self, schema_id: str):
        """Trigger reprocessing of documents with a new schema."""
        # Stub implementation
        pass
    
    async def _generate_candidates(
        self, 
        goal_id: str, 
        document: Document
    ) -> List[Schema]:
        """Generate multiple schema candidates."""
        # Stub - would generate maximalist, minimalist, and balanced schemas
        return []
    
    async def _evaluate_candidates(
        self, 
        candidates: List[Schema], 
        document: Document
    ) -> List[dict]:
        """Evaluate schema candidates against design principles."""
        # Stub - would use Critic to evaluate each schema
        return []
    
    def _select_winner(
        self, 
        candidates: List[Schema], 
        evaluations: List[dict]
    ) -> Schema:
        """Select the best schema candidate."""
        # Stub - would use referee logic to pick winner
        return candidates[0]
    
    async def _create_evolved_schema(
        self, 
        base_schema: Schema, 
        new_fields: List[FieldCandidate]
    ) -> Schema:
        """Create an evolved version of a schema."""
        # Stub - would merge new fields into existing schema
        return base_schema