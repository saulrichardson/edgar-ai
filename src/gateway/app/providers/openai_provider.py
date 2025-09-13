"""OpenAI provider implementation."""

from typing import Dict, Any, List

from openai import AsyncOpenAI

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def chat_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chat completion using OpenAI API."""
        # Remove any custom metadata before forwarding
        request_copy = request.copy()
        request_copy.pop("metadata", None)
        
        # Make API call
        response = await self.client.chat.completions.create(**request_copy)
        
        # Convert to dict
        return response.model_dump()
    
    async def list_models(self) -> List[str]:
        """List available OpenAI models."""
        # Return commonly used models
        # In production, could query the models endpoint
        return [
            "gpt-4-turbo-preview",
            "gpt-4-1106-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-1106",
        ]
    
    async def close(self):
        """Close the OpenAI client."""
        await self.client.close()