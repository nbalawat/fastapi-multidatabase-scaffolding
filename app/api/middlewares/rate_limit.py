import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings
from app.core.logging import get_logger

# Get a logger for the rate limiting middleware
logger = get_logger("rate_limit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests.
    
    This middleware implements a simple in-memory rate limiting strategy
    based on client IP address. For production use, consider using a
    distributed rate limiter with Redis or similar.
    """
    
    def __init__(self, app, settings: Settings):
        """Initialize the rate limiting middleware.
        
        Args:
            app: The FastAPI application
            settings: Application settings containing rate limiting configuration
        """
        super().__init__(app)
        self.settings = settings
        self.requests_per_timeframe = settings.rate_limit_requests
        self.timeframe = settings.rate_limit_timeframe
        
        # Store client request counts and timestamps
        # Format: {client_id: [(timestamp1, count1), (timestamp2, count2), ...]}
        self.client_requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through the middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the next middleware or route handler,
            or a 429 Too Many Requests response if rate limited
        """
        # Get the client ID (IP address)
        client_id = self._get_client_id(request)
        
        # Check if the client has exceeded the rate limit
        if self._is_rate_limited(client_id):
            # Log the rate limiting event
            logger.warning("Rate limit exceeded", client_id=client_id)
            
            # Return a 429 Too Many Requests response
            return Response(
                content='{"detail": "Rate limit exceeded. Try again later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )
        
        # Proceed with the request
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get the client ID from the request.
        
        This method tries to get the client IP address from various headers
        that might be set by proxies, falling back to the client host.
        
        Args:
            request: The incoming request
            
        Returns:
            The client ID (IP address)
        """
        # Try to get the client IP from headers that might be set by proxies
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, use the first one
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to the client host
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if the client has exceeded the rate limit.
        
        Args:
            client_id: The client ID (IP address)
            
        Returns:
            True if the client has exceeded the rate limit, False otherwise
        """
        # Get the current time
        current_time = time.time()
        
        # Remove expired entries
        self.client_requests[client_id] = [
            (timestamp, count) for timestamp, count in self.client_requests[client_id]
            if current_time - timestamp < self.timeframe
        ]
        
        # Calculate the total requests in the current timeframe
        total_requests = sum(count for _, count in self.client_requests[client_id])
        
        # Check if the client has exceeded the rate limit
        if total_requests >= self.requests_per_timeframe:
            return True
        
        # Add the current request to the client's history
        self.client_requests[client_id].append((current_time, 1))
        
        return False
