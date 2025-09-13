"""Critic service for evaluating extraction quality."""

import json
from typing import List

from interfaces.models import Document, Row, Schema, CriticNote
from gateway.client import GatewayClient
from edgar.config import settings


class Critic:
    """
    Evaluates extraction quality and provides feedback.
    
    The Critic:
    - Re-reads the original document
    - Grades each extracted value
    - Identifies patterns in errors
    - Generates improvement suggestions
    """
    
    def __init__(self):
        self.client = GatewayClient()
        self.model = settings.critic_model
    
    async def evaluate(
        self, 
        document: Document, 
        rows: List[Row], 
        schema: Schema
    ) -> List[CriticNote]:
        """
        Evaluate extracted data quality.
        
        Args:
            document: Original document
            rows: Extracted data
            schema: Schema used for extraction
            
        Returns:
            List of critic notes with feedback
        """
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(document, rows, schema)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
            metadata={
                "persona": "critic",
                "document_id": document.id,
                "schema_id": schema.id
            }
        )
        
        # Parse response into CriticNote objects
        evaluation_data = json.loads(response.choices[0].message.content)
        return self._parse_critic_notes(evaluation_data)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the critic."""
        return """You are a meticulous quality auditor for financial data extraction.
        
        Your task is to evaluate the accuracy and completeness of extracted data
        by comparing it against the source document.
        
        For each extracted value, provide:
        1. A score from 0.0 to 1.0 (1.0 = perfect)
        2. Specific feedback on any issues
        3. Suggestions for improvement
        
        Common issues to check:
        - Missing information that exists in the document
        - Incorrect values or misinterpretation
        - Formatting inconsistencies
        - Hallucinated data not in the source
        
        Output your evaluation as a JSON object."""
    
    def _build_evaluation_prompt(
        self, 
        document: Document, 
        rows: List[Row], 
        schema: Schema
    ) -> str:
        """Build the evaluation prompt."""
        # Format extracted data
        extracted_data = []
        for i, row in enumerate(rows):
            extracted_data.append(f"Row {i+1}: {json.dumps(row.data, indent=2)}")
        
        return f"""Evaluate this data extraction:
        
        ORIGINAL DOCUMENT:
        {document.text[:30000]}
        
        EXTRACTION SCHEMA:
        {schema.name}: {schema.description}
        Fields: {[f.name for f in schema.fields]}
        
        EXTRACTED DATA:
        {chr(10).join(extracted_data)}
        
        Evaluate each field in each row for accuracy and completeness."""
    
    def _parse_critic_notes(self, evaluation_data: dict) -> List[CriticNote]:
        """Parse evaluation data into CriticNote objects."""
        notes = []
        
        for row_eval in evaluation_data.get("rows", []):
            row_index = row_eval.get("row_index", 0)
            
            for field_eval in row_eval.get("fields", []):
                note = CriticNote(
                    row_index=row_index,
                    field_name=field_eval.get("field"),
                    score=field_eval.get("score", 0.5),
                    feedback=field_eval.get("feedback", ""),
                    suggestion=field_eval.get("suggestion", ""),
                    severity=self._determine_severity(field_eval.get("score", 0.5))
                )
                notes.append(note)
        
        return notes
    
    def _determine_severity(self, score: float) -> str:
        """Determine severity based on score."""
        if score >= 0.9:
            return "info"
        elif score >= 0.7:
            return "warning"
        else:
            return "error"