"""Goal Setter service for determining extraction objectives."""

from typing import Optional

from interfaces.models import Document, Goal
from gateway.client import GatewayClient
from edgar.config import settings


class GoalSetter:
    """
    Determines the primary analytical objective for a document.
    
    The Goal Setter reads only the document text and decides what information
    would be most valuable to extract, without any predefined rules or templates.
    """
    
    def __init__(self):
        self.client = GatewayClient()
        self.model = settings.goal_setter_model
    
    async def determine_goal(self, document: Document) -> Goal:
        """
        Determine the extraction goal for a document.
        
        Args:
            document: The document to analyze
            
        Returns:
            Goal object describing what to extract
        """
        prompt = self._build_prompt(document)
        
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
            metadata={"persona": "goal_setter", "document_id": document.id}
        )
        
        # Parse response into Goal object
        goal_data = response.choices[0].message.content
        return Goal.model_validate_json(goal_data)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for goal setting."""
        return """You are an expert financial analyst determining what information 
        to extract from SEC filings. Your task is to identify the single most 
        valuable analytical objective for the given document.
        
        Output a JSON object with:
        - goal_id: A unique identifier for this type of extraction
        - overview: One sentence describing the extraction objective
        - topics: List of 3-5 key topics to extract
        - fields: Array of specific fields with name and type
        
        Focus on information that would be most useful for financial analysis,
        risk assessment, or regulatory compliance."""
    
    def _build_prompt(self, document: Document) -> str:
        """Build the prompt for goal determination."""
        # Truncate document if too long
        max_chars = 50000
        text = document.text[:max_chars]
        if len(document.text) > max_chars:
            text += "\n\n[Document truncated...]"
        
        return f"""Analyze this SEC filing and determine the most valuable 
        information to extract:
        
        {text}
        
        What is the single most important analytical objective for this document?"""