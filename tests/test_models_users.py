import pytest
from pydantic import ValidationError

from app.models.users import User, UserInDB, Role


def test_role_enum():
    """Test that Role enum has the expected values."""
    assert Role.ADMIN.value == "admin"
    assert Role.USER.value == "user"
    assert Role.GUEST.value == "guest"


def test_user_model():
    """Test that User model validates correctly."""
    # Valid user
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role=Role.USER
    )
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.role == Role.USER
    
    # Invalid email
    with pytest.raises(ValidationError):
        User(
            username="testuser",
            email="invalid-email",
            full_name="Test User",
            role=Role.USER
        )


def test_user_in_db_model():
    """Test that UserInDB model validates correctly."""
    # Valid user
    user = UserInDB(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role=Role.USER,
        hashed_password="hashed_password_string"
    )
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashed_password_string"
    
    # Test that password is not included in dict representation
    user_dict = user.model_dump()
    assert "hashed_password" not in user_dict
