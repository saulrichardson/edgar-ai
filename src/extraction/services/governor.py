"""Governor service for quality control and promotion decisions."""

from typing import List

from interfaces.models import Row, CriticNote, GovernorDecision
from edgar.config import settings


class Governor:
    """
    Enforces quality gates and manages promotion decisions.
    
    The Governor:
    - Enforces minimum quality thresholds
    - Manages champion/challenger testing
    - Decides when to promote new prompts
    - Triggers back-correction when needed
    """
    
    def __init__(self):
        self.quality_threshold = 0.85
        self.promotion_sample_size = settings.champion_challenger_min_samples
    
    async def evaluate(
        self,
        rows: List[Row],
        critic_notes: List[CriticNote]
    ) -> GovernorDecision:
        """
        Make a governance decision on extraction results.
        
        Args:
            rows: Extracted data
            critic_notes: Critic feedback
            
        Returns:
            GovernorDecision with approval status and actions
        """
        # Calculate quality score
        quality_score = self._calculate_quality_score(critic_notes)
        
        # Determine decision
        if quality_score >= self.quality_threshold:
            status = "approved"
            actions = []
        elif quality_score >= 0.7:
            status = "conditional"
            actions = ["review_required", "improvement_suggested"]
        else:
            status = "rejected"
            actions = ["reprocess", "escalate"]
        
        # Check for systematic issues
        if self._has_systematic_issues(critic_notes):
            actions.append("trigger_prompt_improvement")
        
        return GovernorDecision(
            status=status,
            quality_score=quality_score,
            actions=actions,
            feedback=self._generate_feedback(quality_score, critic_notes)
        )
    
    def _calculate_quality_score(self, critic_notes: List[CriticNote]) -> float:
        """Calculate overall quality score from critic notes."""
        if not critic_notes:
            return 1.0
        
        scores = [note.score for note in critic_notes if note.score is not None]
        if not scores:
            return 0.5
        
        # Weighted average giving more weight to errors
        total_score = 0
        total_weight = 0
        
        for score in scores:
            weight = 1.0 if score >= 0.8 else 2.0  # Double weight for errors
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight
    
    def _has_systematic_issues(self, critic_notes: List[CriticNote]) -> bool:
        """Check if there are systematic issues requiring prompt improvement."""
        # Count errors by field
        field_errors = {}
        for note in critic_notes:
            if note.score and note.score < 0.7:
                field_errors[note.field_name] = field_errors.get(note.field_name, 0) + 1
        
        # If any field has multiple errors, it's systematic
        return any(count >= 3 for count in field_errors.values())
    
    def _generate_feedback(
        self,
        quality_score: float,
        critic_notes: List[CriticNote]
    ) -> str:
        """Generate human-readable feedback."""
        if quality_score >= self.quality_threshold:
            return "Extraction meets quality standards."
        
        # Summarize main issues
        issues = []
        for note in critic_notes:
            if note.score and note.score < 0.7:
                issues.append(f"- {note.field_name}: {note.feedback}")
        
        if issues:
            return f"Quality issues detected:\n" + "\n".join(issues[:5])
        else:
            return "Extraction quality below threshold."