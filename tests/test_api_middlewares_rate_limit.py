import time
from unittest.mock import patch

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.middlewares.rate_limit import RateLimitMiddleware
from app.core.config import Settings


@pytest.fixture
def app():
    """Create a test FastAPI application with rate limiting middleware."""
    app = FastAPI()
    
    # Add rate limiting middleware
    settings = Settings(rate_limit_requests=2, rate_limit_timeframe=5)
    app.add_middleware(RateLimitMiddleware, settings=settings)
    
    # Add a test endpoint
    @app.get("/test")
    async def test_endpoint():
        return {"message": "Test endpoint"}
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


def test_rate_limit_not_exceeded(client):
    """Test that requests below the rate limit are allowed."""
    # Make requests within the rate limit
    response1 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.1"})
    response2 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.1"})
    
    # Both requests should succeed
    assert response1.status_code == 200
    assert response2.status_code == 200


def test_rate_limit_exceeded(client):
    """Test that requests exceeding the rate limit are blocked."""
    # Make requests exceeding the rate limit
    response1 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.2"})
    response2 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.2"})
    response3 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.2"})
    
    # First two requests should succeed, third should be rate limited
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 429
    assert "Rate limit exceeded" in response3.json()["detail"]


def test_rate_limit_different_clients(client):
    """Test that rate limits are applied per client."""
    # Make requests from different clients
    response1 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.3"})
    response2 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.4"})
    response3 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.3"})
    response4 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.4"})
    
    # All requests should succeed as they're from different clients
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200
    assert response4.status_code == 200


def test_rate_limit_reset(client):
    """Test that rate limits reset after the timeframe."""
    # Make initial requests
    response1 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.5"})
    response2 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.5"})
    
    # Both should succeed
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Third request should be rate limited
    response3 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.5"})
    assert response3.status_code == 429
    
    # Mock time.time() to simulate waiting for the rate limit to reset
    with patch("time.time") as mock_time:
        # Set time to 6 seconds in the future (beyond the 5 second timeframe)
        mock_time.return_value = time.time() + 6
        
        # After the timeframe, the rate limit should reset
        response4 = client.get("/test", headers={"X-Forwarded-For": "127.0.0.5"})
        assert response4.status_code == 200
