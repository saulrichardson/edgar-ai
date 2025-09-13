"""Retry middleware for handling transient failures."""

import asyncio
import random
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings


class RetryMiddleware(BaseHTTPMiddleware):
    """Middleware for intelligent retry logic with exponential backoff."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with retry logic."""
        # Only apply retry logic to LLM endpoints
        if request.url.path not in ["/v1/chat/completions"]:
            return await call_next(request)
        
        max_retries = settings.max_retries
        base_delay = settings.retry_delay_ms / 1000  # Convert to seconds
        
        for attempt in range(max_retries + 1):
            try:
                response = await call_next(request)
                
                # Check if we should retry based on status code
                if response.status_code in [429, 503] and attempt < max_retries:
                    # Calculate delay with exponential backoff and jitter
                    delay = self._calculate_delay(attempt, base_delay)
                    
                    # Log retry attempt
                    print(f"[RETRY] Attempt {attempt + 1}/{max_retries}, "
                          f"status={response.status_code}, delay={delay:.2f}s")
                    
                    await asyncio.sleep(delay)
                    continue
                
                return response
                
            except Exception as e:
                if attempt < max_retries:
                    delay = self._calculate_delay(attempt, base_delay)
                    print(f"[RETRY] Attempt {attempt + 1}/{max_retries}, "
                          f"error={str(e)}, delay={delay:.2f}s")
                    await asyncio.sleep(delay)
                else:
                    raise
        
        # Should never reach here
        return response
    
    def _calculate_delay(self, attempt: int, base_delay: float) -> float:
        """Calculate delay with exponential backoff and jitter."""
        # Exponential backoff: base_delay * 2^attempt
        exponential_delay = base_delay * (2 ** attempt)
        
        # Add jitter (±25% of the delay)
        jitter = exponential_delay * 0.25 * (2 * random.random() - 1)
        
        # Apply max delay cap
        max_delay = settings.retry_max_delay_ms / 1000
        return min(exponential_delay + jitter, max_delay)