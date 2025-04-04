import os
from unittest import mock

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_default_values():
    """Test that default settings are loaded correctly."""
    settings = Settings()
    assert settings.app_name == "FastAPI Multiple Databases"
    assert settings.debug is False
    assert settings.api_prefix == "/api"
    assert settings.db_type == "postgres"


def test_settings_from_env_vars():
    """Test that settings can be overridden by environment variables."""
    with mock.patch.dict(
        os.environ,
        {
            "APP_NAME": "Custom App Name",
            "DEBUG": "true",
            "API_PREFIX": "/custom-api",
            "DB_TYPE": "mongodb",
        },
    ):
        settings = Settings()
        assert settings.app_name == "Custom App Name"
        assert settings.debug is True
        assert settings.api_prefix == "/custom-api"
        assert settings.db_type == "mongodb"


def test_db_type_validation():
    """Test that db_type is validated against allowed values."""
    with mock.patch.dict(os.environ, {"DB_TYPE": "invalid_db"}):
        with pytest.raises(ValidationError):
            Settings()


def test_get_settings():
    """Test that get_settings returns a Settings instance."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    # Test that it's a singleton
    assert get_settings() is settings
