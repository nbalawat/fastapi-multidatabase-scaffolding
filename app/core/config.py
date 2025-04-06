import os
from functools import lru_cache
from typing import Literal, Optional, Dict, Any, Union

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings.
    
    These settings can be configured via environment variables.
    The configuration supports both Docker and non-Docker environments.
    """
    # Application settings
    app_name: str = "FastAPI Multiple Databases"
    debug: bool = False
    api_prefix: str = "/api"
    
    # Docker settings
    use_docker: bool = False
    
    # Primary database settings
    db_type: Literal["postgres", "sqlserver", "mongodb"] = "postgres"
    
    # PostgreSQL settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "fastapi_db"
    postgres_service: str = "app_postgres"  # Docker service name
    
    # SQL Server settings
    sqlserver_host: str = "localhost"
    sqlserver_port: int = 1433
    sqlserver_user: str = "sa"
    sqlserver_password: str = "YourStrong@Passw0rd"
    sqlserver_db: str = "fastapi_db"
    sqlserver_service: str = "app_sqlserver"  # Docker service name
    
    # MongoDB settings
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_user: str = "mongodb"
    mongodb_password: str = "mongodb"
    mongodb_db: str = "fastapi_db"
    mongodb_service: str = "app_mongodb"  # Docker service name
    mongodb_connection_string: Optional[str] = None
    
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
    
    # Computed properties for database connections
    db_host: str = ""
    db_port: int = 0
    db_user: str = ""
    db_password: str = ""
    db_name: str = ""
    
    @model_validator(mode='after')
    def set_db_connection_params(self) -> 'Settings':
        """Set the database connection parameters based on the selected database type."""
        db_type = self.db_type
        use_docker = self.use_docker
        
        if db_type == "postgres":
            if use_docker:
                self.db_host = self.postgres_service
            else:
                self.db_host = self.postgres_host
            self.db_port = self.postgres_port
            self.db_user = self.postgres_user
            self.db_password = self.postgres_password
            self.db_name = self.postgres_db
        
        elif db_type == "sqlserver":
            if use_docker:
                self.db_host = self.sqlserver_service
            else:
                self.db_host = self.sqlserver_host
            self.db_port = self.sqlserver_port
            self.db_user = self.sqlserver_user
            self.db_password = self.sqlserver_password
            self.db_name = self.sqlserver_db
        
        elif db_type == "mongodb":
            if use_docker:
                self.db_host = self.mongodb_service
            else:
                self.db_host = self.mongodb_host
            self.db_port = self.mongodb_port
            self.db_user = self.mongodb_user
            self.db_password = self.mongodb_password
            self.db_name = self.mongodb_db
            
            # Set MongoDB connection string if not provided
            if not self.mongodb_connection_string:
                # For Docker environments, use the service name directly with authSource=admin
                if use_docker:
                    self.mongodb_connection_string = f"mongodb://{self.db_user}:{self.db_password}@mongodb:27017/{self.db_name}?authSource=admin"
                else:
                    self.mongodb_connection_string = f"mongodb://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        
        return self
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in the environment


@lru_cache
def get_settings() -> Settings:
    """Return the application settings as a singleton.
    
    Uses environment variables from .env file or system environment.
    """
    return Settings()


def get_db_connection_info() -> Dict[str, Any]:
    """Get the database connection information based on the current settings.
    
    Returns:
        A dictionary with connection parameters for the configured database.
    """
    settings = get_settings()
    
    connection_info = {
        "db_type": settings.db_type,
        "host": settings.db_host,
        "port": settings.db_port,
        "user": settings.db_user,
        "password": settings.db_password,
        "database": settings.db_name,
    }
    
    # Add database-specific connection info
    if settings.db_type == "mongodb" and settings.mongodb_connection_string:
        connection_info["connection_string"] = settings.mongodb_connection_string
    
    return connection_info
