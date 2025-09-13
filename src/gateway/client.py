"""Client for the Edgar-AI Gateway."""

import httpx
from typing import Dict, Any, Optional

from edgar.config import settings


class GatewayClient:
    """Client for interacting with the Edgar-AI Gateway."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.gateway_url
        self.timeout = settings.gateway_timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )
        
        # Nested interface for OpenAI compatibility
        self.chat = ChatInterface(self)
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class ChatInterface:
    """Chat interface for OpenAI compatibility."""
    
    def __init__(self, client: GatewayClient):
        self.client = client
        self.completions = CompletionsInterface(client)


class CompletionsInterface:
    """Completions interface for OpenAI compatibility."""
    
    def __init__(self, client: GatewayClient):
        self.client = client
    
    async def create(self, **kwargs) -> Dict[str, Any]:
        """
        Create a chat completion.
        
        Mirrors the OpenAI API interface.
        """
        response = await self.client.client.post(
            "/v1/chat/completions",
            json=kwargs
        )
        response.raise_for_status()
        return response.json()