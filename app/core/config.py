from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings.
    
    These settings can be configured via environment variables.
    """
    # Application settings
    app_name: str = "FastAPI Multiple Databases"
    debug: bool = False
    api_prefix: str = "/api"
    
    # Database settings
    db_type: Literal["postgres", "mysql", "sqlserver", "mongodb"] = "postgres"
    db_host: str = "localhost"
    db_port: int = Field(default=5432)  # Default PostgreSQL port
    db_user: str = "postgres"
    db_password: str = ""
    db_name: str = "fastapi_db"
    
    # MongoDB specific settings (only used if db_type is mongodb)
    mongodb_connection_string: Optional[str] = None
    
    # SQL Server specific settings (only used if db_type is sqlserver)
    sqlserver_host: str = Field(default="localhost")
    sqlserver_port: int = Field(default=1433)
    sqlserver_user: str = Field(default="sa")
    sqlserver_password: str = Field(default="YourStrong@Passw0rd")
    sqlserver_db: str = Field(default="fastapi_db")
    
    # JWT settings
    jwt_secret_key: str = "change_this_in_production"
    jwt_algorithm: str = "HS256"
    jwt_token_expire_minutes: int = 60 * 24  # 1 day
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_timeframe: int = 60  # seconds
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    
    # Admin user settings
    admin_email: str = "admin@example.com"
    admin_username: str = "admin"
    admin_password: str = "admin123"  # Change this in production
    
    @field_validator("db_port")
    def validate_db_port(cls, v: int, values) -> int:
        """Validate and set the correct default port based on the database type."""
        db_type = values.data.get("db_type")
        if db_type == "mysql" and v == 5432:
            return 3306  # Default MySQL port
        elif db_type == "sqlserver" and v == 5432:
            return 1433  # Default SQL Server port
        elif db_type == "mongodb" and v == 5432:
            return 27017  # Default MongoDB port
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return the application settings as a singleton."""
    return Settings()
