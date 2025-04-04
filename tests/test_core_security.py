import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from jose import jwt

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    # Verify that the hash is different from the original password
    assert hashed != password
    
    # Verify that the password verifies correctly
    assert verify_password(password, hashed) is True
    
    # Verify that an incorrect password fails
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    """Test JWT token creation."""
    # Mock settings
    settings = Settings(
        jwt_secret_key="testsecret",
        jwt_algorithm="HS256",
        jwt_token_expire_minutes=30
    )
    
    # Create a token
    data = {"sub": "testuser", "role": "admin"}
    token = create_access_token(data, settings)
    
    # Decode the token and verify its contents
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    
    assert payload["sub"] == "testuser"
    assert payload["role"] == "admin"
    assert "exp" in payload  # Expiration time should be set


def test_create_access_token_with_expiration():
    """Test JWT token creation with custom expiration."""
    # Mock settings
    settings = Settings(
        jwt_secret_key="testsecret",
        jwt_algorithm="HS256",
    )
    
    # Create a token with custom expiration
    expires_delta = timedelta(minutes=5)
    data = {"sub": "testuser"}
    token = create_access_token(data, settings, expires_delta=expires_delta)
    
    # Decode the token and verify its expiration
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    
    # Calculate expected expiration time (with some tolerance for test execution time)
    now = datetime.utcnow().timestamp()
    expected_exp = now + expires_delta.total_seconds()
    
    # Allow for a small difference due to execution time
    assert abs(payload["exp"] - expected_exp) < 5  # Within 5 seconds


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    """Test getting the current user with a valid token."""
    # Mock settings
    settings = Settings(
        jwt_secret_key="testsecret",
        jwt_algorithm="HS256",
    )
    
    # Create a valid token
    user_data = {"sub": "testuser", "role": "admin"}
    token = create_access_token(user_data, settings)
    
    # Mock the get_settings function
    with patch("app.core.security.get_settings", return_value=settings):
        # Get the current user
        user = await get_current_user(token)
        
        # Verify the user data
        assert user["username"] == "testuser"
        assert user["role"] == "admin"


@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    """Test getting the current user with an expired token."""
    # Mock settings
    settings = Settings(
        jwt_secret_key="testsecret",
        jwt_algorithm="HS256",
    )
    
    # Create an expired token
    user_data = {"sub": "testuser"}
    expires_delta = timedelta(seconds=-1)  # Expired 1 second ago
    token = create_access_token(user_data, settings, expires_delta=expires_delta)
    
    # Mock the get_settings function
    with patch("app.core.security.get_settings", return_value=settings):
        # Attempt to get the current user with the expired token
        with pytest.raises(HTTPException) as excinfo:
            await get_current_user(token)
        
        # Verify the exception
        assert excinfo.value.status_code == 401
        assert "Token has expired" in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test getting the current user with an invalid token."""
    # Mock settings
    settings = Settings(
        jwt_secret_key="testsecret",
        jwt_algorithm="HS256",
    )
    
    # Create an invalid token
    token = "invalid.token.format"
    
    # Mock the get_settings function
    with patch("app.core.security.get_settings", return_value=settings):
        # Attempt to get the current user with the invalid token
        with pytest.raises(HTTPException) as excinfo:
            await get_current_user(token)
        
        # Verify the exception
        assert excinfo.value.status_code == 401
        assert "Could not validate credentials" in excinfo.value.detail
