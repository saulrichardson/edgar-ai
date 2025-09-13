"""Main orchestrator for the extraction pipeline."""

from typing import List, Optional
import asyncio

from interfaces.models import Document, ExtractionResult, Schema
from storage.memory import MemoryStore
from .services.goal_setter import GoalSetter
from .services.schema_evolution import SchemaEvolution
from .services.prompt_builder import PromptBuilder
from .services.extractor import Extractor
from .services.critic import Critic
from .services.tutor import Tutor
from .services.governor import Governor


class ExtractionPipeline:
    """Orchestrates the document extraction pipeline."""
    
    def __init__(self):
        self.memory = MemoryStore()
        self.goal_setter = GoalSetter()
        self.schema_evolution = SchemaEvolution()
        self.prompt_builder = PromptBuilder()
        self.extractor = Extractor()
        self.critic = Critic()
        self.tutor = Tutor()
        self.governor = Governor()
    
    async def process(self, document: Document) -> ExtractionResult:
        """
        Process a single document through the extraction pipeline.
        
        Args:
            document: The document to process
            
        Returns:
            ExtractionResult containing extracted data and metadata
        """
        # Step 1: Determine extraction goal
        goal = await self.goal_setter.determine_goal(document)
        
        # Step 2: Get or create schema
        schema = await self._get_or_create_schema(goal.goal_id, document)
        
        # Step 3: Build extraction prompt
        prompt = await self.prompt_builder.build(schema, document)
        
        # Step 4: Extract structured data
        rows = await self.extractor.extract(prompt, document)
        
        # Step 5: Critique extraction quality
        critic_notes = await self.critic.evaluate(document, rows, schema)
        
        # Step 6: Generate improvements (if needed)
        if self._should_improve(critic_notes):
            improvements = await self.tutor.suggest_improvements(
                schema, prompt, critic_notes
            )
            # Queue improvements for testing
            await self.memory.queue_improvements(improvements)
        
        # Step 7: Governor decision
        decision = await self.governor.evaluate(rows, critic_notes)
        
        # Step 8: Update memory
        await self.memory.record_extraction(
            document_id=document.id,
            goal_id=goal.goal_id,
            schema_id=schema.id,
            rows=rows,
            critic_notes=critic_notes,
            decision=decision
        )
        
        return ExtractionResult(
            document_id=document.id,
            goal=goal,
            schema=schema,
            rows=rows,
            critic_notes=critic_notes,
            decision=decision
        )
    
    async def process_batch(
        self, 
        documents: List[Document], 
        max_concurrent: int = 5
    ) -> List[ExtractionResult]:
        """Process multiple documents concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_limit(doc: Document) -> ExtractionResult:
            async with semaphore:
                return await self.process(doc)
        
        tasks = [process_with_limit(doc) for doc in documents]
        return await asyncio.gather(*tasks)
    
    async def _get_or_create_schema(
        self, 
        goal_id: str, 
        document: Document
    ) -> Schema:
        """Get existing schema or create new one."""
        # Try warm start
        existing_schema = await self.memory.find_schema(goal_id)
        if existing_schema:
            return existing_schema
        
        # Cold start - create new schema
        return await self.schema_evolution.create_schema(goal_id, document)
    
    def _should_improve(self, critic_notes: List) -> bool:
        """Determine if improvements are needed based on critic feedback."""
        if not critic_notes:
            return False
        
        # Calculate average score
        scores = [note.score for note in critic_notes if note.score is not None]
        if not scores:
            return False
        
        avg_score = sum(scores) / len(scores)
        return avg_score < 0.8  # Threshold for improvement
    
    def to_dataframe(self, results: List[ExtractionResult]):
        """Convert extraction results to pandas DataFrame."""
        # Stub - would implement DataFrame conversion
        pass