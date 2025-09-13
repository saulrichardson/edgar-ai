"""Logging middleware for request/response tracking."""

import json
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured logging of all gateway requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Extract request info
        if request.url.path == "/v1/chat/completions":
            body = await request.body()
            request_data = json.loads(body) if body else {}
            
            # Log request (without sensitive content)
            self._log_request(request_id, request_data)
            
            # Restore body for downstream processing
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response metadata
        self._log_response(request_id, response.status_code, duration)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    def _log_request(self, request_id: str, data: dict):
        """Log request details."""
        log_entry = {
            "type": "request",
            "request_id": request_id,
            "model": data.get("model"),
            "persona": data.get("metadata", {}).get("persona"),
            "message_count": len(data.get("messages", [])),
            "has_tools": bool(data.get("tools")),
        }
        
        if settings.record_sessions:
            # Save full request for debugging
            self._save_session_data(request_id, "request", data)
        
        print(f"[GATEWAY] {json.dumps(log_entry)}")
    
    def _log_response(self, request_id: str, status_code: int, duration: float):
        """Log response details."""
        log_entry = {
            "type": "response",
            "request_id": request_id,
            "status_code": status_code,
            "duration_seconds": round(duration, 3),
        }
        
        print(f"[GATEWAY] {json.dumps(log_entry)}")
    
    def _save_session_data(self, request_id: str, data_type: str, data: dict):
        """Save session data for debugging."""
        # Stub - would implement file writing in production
        pass