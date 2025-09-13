"""Base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class LLMProvider(ABC):
    """Abstract base class for LLM provider implementations."""
    
    @abstractmethod
    async def chat_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a chat completion.
        
        Args:
            request: OpenAI-compatible chat completion request
            
        Returns:
            OpenAI-compatible chat completion response
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """
        List available models from this provider.
        
        Returns:
            List of model IDs
        """
        pass
    
    async def close(self):
        """Clean up provider resources."""
        pass