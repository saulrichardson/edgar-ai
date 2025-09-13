"""Breaker service for adversarial testing."""

from typing import List

from interfaces.models import Document, Schema
from gateway.client import GatewayClient
from edgar.config import settings


class Breaker:
    """
    Generates adversarial test cases to strengthen the extraction system.
    
    The Breaker:
    - Creates synthetic documents designed to break extractors
    - Tests edge cases before they appear in production
    - Forces continuous improvement
    - Ensures robustness
    """
    
    def __init__(self):
        self.client = GatewayClient()
        self.enabled = settings.enable_adversarial_testing
    
    async def generate_adversarial_cases(
        self,
        schema: Schema,
        known_failures: List[dict]
    ) -> List[Document]:
        """
        Generate adversarial test documents.
        
        Args:
            schema: Schema to test against
            known_failures: Previous extraction failures
            
        Returns:
            List of synthetic test documents
        """
        if not self.enabled:
            return []
        
        # Analyze failure patterns
        patterns = self._analyze_failures(known_failures)
        
        # Generate test cases for each pattern
        test_cases = []
        for pattern in patterns:
            doc = await self._generate_test_case(schema, pattern)
            if doc:
                test_cases.append(doc)
        
        # Add random edge cases
        edge_cases = await self._generate_edge_cases(schema)
        test_cases.extend(edge_cases)
        
        return test_cases
    
    async def _generate_test_case(
        self,
        schema: Schema,
        pattern: dict
    ) -> Document:
        """Generate a test case for a specific failure pattern."""
        prompt = f"""Generate a synthetic financial document that would be 
        challenging to extract {schema.name} information from.
        
        Focus on this specific challenge: {pattern['description']}
        
        The document should:
        1. Look realistic
        2. Contain edge cases for {pattern['affected_fields']}
        3. Test the extraction system's robustness
        
        Generate only the document text, no explanation."""
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You generate challenging test documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            metadata={"persona": "breaker", "schema_id": schema.id}
        )
        
        return Document(
            id=f"synthetic_{pattern['type']}_{schema.id}",
            text=response.choices[0].message.content,
            metadata={
                "synthetic": True,
                "pattern": pattern['type'],
                "schema_id": schema.id
            }
        )
    
    async def _generate_edge_cases(self, schema: Schema) -> List[Document]:
        """Generate random edge case documents."""
        edge_case_types = [
            "extremely_long_document",
            "heavily_formatted_tables",
            "mixed_languages",
            "ambiguous_values",
            "nested_structures"
        ]
        
        # Stub - would generate various edge cases
        return []
    
    def _analyze_failures(self, known_failures: List[dict]) -> List[dict]:
        """Analyze known failures to identify patterns."""
        patterns = []
        
        # Group failures by type
        failure_groups = {}
        for failure in known_failures:
            failure_type = failure.get("type", "unknown")
            if failure_type not in failure_groups:
                failure_groups[failure_type] = []
            failure_groups[failure_type].append(failure)
        
        # Create pattern for each group
        for failure_type, failures in failure_groups.items():
            affected_fields = list(set(
                f.get("field") for f in failures if f.get("field")
            ))
            
            patterns.append({
                "type": failure_type,
                "description": f"Common {failure_type} failures",
                "affected_fields": affected_fields,
                "count": len(failures)
            })
        
        return patterns