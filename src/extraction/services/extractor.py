"""Extractor service for executing structured data extraction."""

from typing import List
import json

from interfaces.models import Document, Prompt, Row
from gateway.client import GatewayClient
from edgar.config import settings


class Extractor:
    """
    Executes structured data extraction using LLMs.
    
    Features:
    - Large-context document processing
    - Function calling for structured output
    - Automatic validation and retry
    - Full lineage tracking
    """
    
    def __init__(self):
        self.client = GatewayClient()
        self.model = settings.extractor_model
        self.max_retries = settings.max_extraction_retries
    
    async def extract(self, prompt: Prompt, document: Document) -> List[Row]:
        """
        Extract structured data from a document.
        
        Args:
            prompt: The extraction prompt with schema
            document: The document to extract from
            
        Returns:
            List of extracted rows
        """
        messages = [
            {"role": "system", "content": prompt.system_prompt},
            {"role": "user", "content": prompt.user_prompt}
        ]
        
        tools = [{
            "type": "function",
            "function": prompt.function_schema
        }]
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice={"type": "function", "function": {"name": "extract_data"}},
                    temperature=settings.extraction_temperature,
                    metadata={
                        "persona": "extractor",
                        "document_id": document.id,
                        "schema_id": prompt.schema_id,
                        "attempt": attempt + 1
                    }
                )
                
                # Parse function call response
                rows = self._parse_extraction(response)
                
                # Validate and return
                return self._validate_rows(rows, prompt.function_schema)
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                # Log and retry
                print(f"Extraction attempt {attempt + 1} failed: {e}")
        
        return []
    
    def _parse_extraction(self, response) -> List[Row]:
        """Parse LLM response into Row objects."""
        tool_calls = response.choices[0].message.tool_calls
        
        if not tool_calls:
            return []
        
        # Get the function call arguments
        function_args = json.loads(tool_calls[0].function.arguments)
        rows_data = function_args.get("rows", [])
        
        # Convert to Row objects
        rows = []
        for row_data in rows_data:
            row = Row(
                schema_id=None,  # Will be set by orchestrator
                data=row_data,
                metadata={
                    "model": self.model,
                    "extraction_timestamp": None,  # Will be set
                }
            )
            rows.append(row)
        
        return rows
    
    def _validate_rows(self, rows: List[Row], schema: dict) -> List[Row]:
        """Validate extracted rows against schema."""
        # Basic validation - in production would be more thorough
        properties = schema["parameters"]["properties"]["rows"]["items"]["properties"]
        required = schema["parameters"]["properties"]["rows"]["items"].get("required", [])
        
        validated_rows = []
        for row in rows:
            # Check required fields
            missing = [field for field in required if field not in row.data]
            if missing:
                print(f"Warning: Row missing required fields: {missing}")
                continue
            
            # Check field types
            valid = True
            for field, value in row.data.items():
                if field not in properties:
                    print(f"Warning: Unknown field: {field}")
                    continue
                
                expected_type = properties[field]["type"]
                if not self._check_type(value, expected_type):
                    print(f"Warning: Field {field} has wrong type")
                    valid = False
            
            if valid:
                validated_rows.append(row)
        
        return validated_rows
    
    def _check_type(self, value, expected_type: str) -> bool:
        """Check if value matches expected type."""
        if value is None:
            return True  # Null is allowed
        
        type_checkers = {
            "string": lambda v: isinstance(v, str),
            "number": lambda v: isinstance(v, (int, float)),
            "boolean": lambda v: isinstance(v, bool),
            "array": lambda v: isinstance(v, list)
        }
        
        checker = type_checkers.get(expected_type, lambda v: True)
        return checker(value)