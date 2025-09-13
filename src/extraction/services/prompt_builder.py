"""Prompt Builder service for converting schemas to extraction prompts."""

from interfaces.models import Document, Schema, Prompt
from edgar.config import settings


class PromptBuilder:
    """
    Converts schemas into optimized extraction prompts.
    
    Features:
    - Dynamic field enumeration based on schema
    - Token budget management for large documents
    - Function-calling format for structured output
    - Persona-specific instructions
    """
    
    def __init__(self):
        self.max_tokens = 100000  # Conservative limit
    
    async def build(self, schema: Schema, document: Document) -> Prompt:
        """
        Build an extraction prompt from a schema and document.
        
        Args:
            schema: The schema defining what to extract
            document: The document to extract from
            
        Returns:
            Prompt object ready for extraction
        """
        # Build system prompt
        system_prompt = self._build_system_prompt(schema)
        
        # Build user prompt with document
        user_prompt = self._build_user_prompt(document, schema)
        
        # Create function schema for structured output
        function_schema = self._build_function_schema(schema)
        
        return Prompt(
            schema_id=schema.id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            function_schema=function_schema,
            token_budget=self.max_tokens
        )
    
    def _build_system_prompt(self, schema: Schema) -> str:
        """Build the system prompt for extraction."""
        return f"""You are a precise data extractor for financial documents.
        
        Your task is to extract information according to the provided schema.
        
        Schema Overview: {schema.description}
        
        Rules:
        1. Extract ONLY information explicitly stated in the document
        2. Use null for missing or unclear values
        3. Preserve exact wording for text fields
        4. Follow the exact field names and types specified
        5. For repeated sections, create multiple rows
        
        You will output your extraction using the provided function schema."""
    
    def _build_user_prompt(self, document: Document, schema: Schema) -> str:
        """Build the user prompt with document content."""
        # Truncate document if needed to fit token budget
        max_doc_chars = 80000  # Rough estimate
        doc_text = document.text[:max_doc_chars]
        
        if len(document.text) > max_doc_chars:
            doc_text += "\n\n[Document truncated for processing...]"
        
        return f"""Extract information from this document according to the schema.
        
        Document:
        {doc_text}
        
        Schema fields to extract:
        {self._format_fields(schema.fields)}
        
        Extract all relevant information, creating multiple rows if needed."""
    
    def _build_function_schema(self, schema: Schema) -> dict:
        """Build OpenAI function schema for structured output."""
        properties = {}
        required = []
        
        for field in schema.fields:
            properties[field.name] = {
                "type": self._map_type(field.type),
                "description": field.description
            }
            if field.required:
                required.append(field.name)
        
        return {
            "name": "extract_data",
            "description": f"Extract {schema.name} information",
            "parameters": {
                "type": "object",
                "properties": {
                    "rows": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": properties,
                            "required": required
                        }
                    }
                },
                "required": ["rows"]
            }
        }
    
    def _format_fields(self, fields: list) -> str:
        """Format field list for prompt."""
        lines = []
        for field in fields:
            line = f"- {field.name} ({field.type}): {field.description}"
            if field.examples:
                line += f" Examples: {', '.join(field.examples)}"
            lines.append(line)
        return "\n".join(lines)
    
    def _map_type(self, field_type: str) -> str:
        """Map schema field type to JSON schema type."""
        type_map = {
            "text": "string",
            "number": "number",
            "currency": "number",
            "percentage": "number",
            "date": "string",
            "boolean": "boolean",
            "array": "array"
        }
        return type_map.get(field_type, "string")