import pytest
from pydantic import ValidationError

from app.schemas.users import UserCreate, UserUpdate, UserResponse, Token, TokenData


def test_user_create_schema():
    """Test that UserCreate schema validates correctly."""
    # Valid user creation
    user = UserCreate(
        username="testuser",
        email="test@example.com",
        password="strongpassword123",
        full_name="Test User"
    )
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.password == "strongpassword123"
    
    # Password too short
    with pytest.raises(ValidationError):
        UserCreate(
            username="testuser",
            email="test@example.com",
            password="short",  # Too short
            full_name="Test User"
        )


def test_user_update_schema():
    """Test that UserUpdate schema validates correctly."""
    # Update with some fields
    user_update = UserUpdate(full_name="New Name")
    assert user_update.full_name == "New Name"
    assert user_update.password is None
    
    # Update with password
    user_update = UserUpdate(password="newstrongpassword123")
    assert user_update.password == "newstrongpassword123"
    
    # Update with invalid password
    with pytest.raises(ValidationError):
        UserUpdate(password="short")  # Too short


def test_user_response_schema():
    """Test that UserResponse schema validates correctly."""
    user = UserResponse(
        id="123",
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role="user",
        is_active=True
    )
    assert user.id == "123"
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.role == "user"


def test_token_schema():
    """Test that Token schema validates correctly."""
    token = Token(
        access_token="some.jwt.token",
        token_type="bearer"
    )
    assert token.access_token == "some.jwt.token"
    assert token.token_type == "bearer"


def test_token_data_schema():
    """Test that TokenData schema validates correctly."""
    token_data = TokenData(
        username="testuser",
        role="admin"
    )
    assert token_data.username == "testuser"
    assert token_data.role == "admin"
    
    # Username is required
    with pytest.raises(ValidationError):
        TokenData(role="admin")  # Missing username
