"""Tutor service for generating prompt improvements."""

from typing import List, Optional

from interfaces.models import Schema, Prompt, CriticNote, Improvement
from gateway.client import GatewayClient
from edgar.config import settings


class Tutor:
    """
    Generates improved prompts based on Critic feedback.
    
    When errors accumulate, the Tutor:
    - Analyzes error patterns
    - Rewrites problematic prompt sections
    - Creates challenger prompts for A/B testing
    - Submits improvements for Governor approval
    """
    
    def __init__(self):
        self.client = GatewayClient()
        self.model = settings.tutor_model
    
    async def suggest_improvements(
        self,
        schema: Schema,
        prompt: Prompt,
        critic_notes: List[CriticNote]
    ) -> Optional[Improvement]:
        """
        Generate prompt improvements based on critic feedback.
        
        Args:
            schema: Current schema
            prompt: Current prompt
            critic_notes: Feedback from critic
            
        Returns:
            Improvement suggestion if warranted
        """
        # Group errors by pattern
        error_patterns = self._analyze_error_patterns(critic_notes)
        
        if not error_patterns:
            return None
        
        # Generate improvement suggestion
        improvement_prompt = self._build_improvement_prompt(
            schema, prompt, error_patterns
        )
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": improvement_prompt
                }
            ],
            temperature=0.3,
            metadata={
                "persona": "tutor",
                "schema_id": schema.id
            }
        )
        
        # Parse and return improvement
        return self._parse_improvement(response, schema, prompt)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the tutor."""
        return """You are an expert prompt engineer specializing in improving
        data extraction prompts based on error patterns.
        
        Your task is to:
        1. Identify the root cause of extraction errors
        2. Suggest specific prompt improvements
        3. Maintain backward compatibility when possible
        4. Focus on clarity and precision
        
        Provide concrete, actionable improvements that address the specific
        issues identified by the critic."""
    
    def _analyze_error_patterns(
        self, 
        critic_notes: List[CriticNote]
    ) -> dict:
        """Analyze critic notes for error patterns."""
        patterns = {
            "missing_values": [],
            "incorrect_values": [],
            "formatting_issues": [],
            "hallucinations": []
        }
        
        for note in critic_notes:
            if note.score < 0.7:  # Focus on significant issues
                if "missing" in note.feedback.lower():
                    patterns["missing_values"].append(note)
                elif "incorrect" in note.feedback.lower():
                    patterns["incorrect_values"].append(note)
                elif "format" in note.feedback.lower():
                    patterns["formatting_issues"].append(note)
                elif "not found" in note.feedback.lower():
                    patterns["hallucinations"].append(note)
        
        # Remove empty patterns
        return {k: v for k, v in patterns.items() if v}
    
    def _build_improvement_prompt(
        self,
        schema: Schema,
        prompt: Prompt,
        error_patterns: dict
    ) -> str:
        """Build prompt for improvement generation."""
        # Format error patterns
        pattern_summary = []
        for pattern_type, notes in error_patterns.items():
            fields = list(set(note.field_name for note in notes))
            pattern_summary.append(
                f"{pattern_type}: {len(notes)} issues affecting {fields}"
            )
        
        return f"""Improve this extraction prompt based on error patterns:
        
        CURRENT PROMPT:
        System: {prompt.system_prompt}
        User template: {prompt.user_prompt[:1000]}...
        
        ERROR PATTERNS:
        {chr(10).join(pattern_summary)}
        
        SPECIFIC ISSUES:
        {self._format_issues(error_patterns)}
        
        Suggest specific improvements to address these issues."""
    
    def _format_issues(self, error_patterns: dict) -> str:
        """Format specific issues for the prompt."""
        issues = []
        for pattern_type, notes in error_patterns.items():
            issues.append(f"\n{pattern_type.upper()}:")
            for note in notes[:3]:  # Limit to top 3 per pattern
                issues.append(f"- Field: {note.field_name}")
                issues.append(f"  Feedback: {note.feedback}")
                issues.append(f"  Suggestion: {note.suggestion}")
        return "\n".join(issues)
    
    def _parse_improvement(
        self,
        response,
        schema: Schema,
        prompt: Prompt
    ) -> Improvement:
        """Parse LLM response into Improvement object."""
        # Stub implementation
        return Improvement(
            schema_id=schema.id,
            prompt_id=prompt.id,
            description="Improved extraction prompt",
            changes=[],
            expected_impact="Higher extraction accuracy",
            test_cases=[]
        )