#!/usr/bin/env python
"""
Environment Setup Script for FastAPI Multiple Databases Project

This script helps set up the environment configuration for the project.
It creates a .env file based on user input or default values.
"""
import os
import shutil
import argparse
from typing import Dict, Any, Optional


def get_user_input(prompt: str, default: Any) -> str:
    """Get user input with a default value."""
    user_input = input(f"{prompt} [default: {default}]: ")
    return user_input if user_input.strip() else str(default)


def create_env_file(use_docker: bool = False, db_type: str = "postgres") -> None:
    """Create a .env file based on user input or default values."""
    # Check if .env file already exists
    if os.path.exists(".env"):
        overwrite = input(".env file already exists. Overwrite? (y/n): ").lower()
        if overwrite != "y":
            print("Setup canceled. Existing .env file was not modified.")
            return
    
    # Copy .env.example to .env if it exists
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        print("Created .env file from .env.example")
    else:
        # Create .env file from scratch
        with open(".env", "w") as f:
            f.write("# Application settings\n")
            f.write(f"APP_NAME=\"{get_user_input('Application name', 'FastAPI Multiple Databases')}\"\n")
            f.write(f"DEBUG={get_user_input('Debug mode', 'false').lower()}\n")
            f.write(f"API_PREFIX=\"{get_user_input('API prefix', '/api')}\"\n")
            f.write("\n")
            
            # Docker settings
            f.write("# Docker settings\n")
            use_docker_input = get_user_input("Use Docker", "true" if use_docker else "false").lower()
            f.write(f"USE_DOCKER={use_docker_input}\n")
            f.write("\n")
            
            # Database type
            f.write("# Primary database settings\n")
            db_type_input = get_user_input("Database type (postgres, sqlserver, mongodb)", db_type).lower()
            f.write(f"DB_TYPE={db_type_input}\n")
            f.write("\n")
            
            # PostgreSQL settings
            f.write("# PostgreSQL settings\n")
            f.write(f"POSTGRES_HOST=\"{get_user_input('PostgreSQL host', 'localhost')}\"\n")
            f.write(f"POSTGRES_PORT={get_user_input('PostgreSQL port', '5432')}\n")
            f.write(f"POSTGRES_USER=\"{get_user_input('PostgreSQL user', 'postgres')}\"\n")
            f.write(f"POSTGRES_PASSWORD=\"{get_user_input('PostgreSQL password', 'postgres')}\"\n")
            f.write(f"POSTGRES_DB=\"{get_user_input('PostgreSQL database', 'fastapi_db')}\"\n")
            f.write(f"POSTGRES_SERVICE=\"{get_user_input('PostgreSQL Docker service name', 'app_postgres')}\"\n")
            f.write("\n")
            
            # SQL Server settings
            f.write("# SQL Server settings\n")
            f.write(f"SQLSERVER_HOST=\"{get_user_input('SQL Server host', 'localhost')}\"\n")
            f.write(f"SQLSERVER_PORT={get_user_input('SQL Server port', '1433')}\n")
            f.write(f"SQLSERVER_USER=\"{get_user_input('SQL Server user', 'sa')}\"\n")
            f.write(f"SQLSERVER_PASSWORD=\"{get_user_input('SQL Server password', 'YourStrong@Passw0rd')}\"\n")
            f.write(f"SQLSERVER_DB=\"{get_user_input('SQL Server database', 'fastapi_db')}\"\n")
            f.write(f"SQLSERVER_SERVICE=\"{get_user_input('SQL Server Docker service name', 'app_sqlserver')}\"\n")
            f.write("\n")
            
            # MongoDB settings
            f.write("# MongoDB settings\n")
            f.write(f"MONGODB_HOST=\"{get_user_input('MongoDB host', 'localhost')}\"\n")
            f.write(f"MONGODB_PORT={get_user_input('MongoDB port', '27017')}\n")
            f.write(f"MONGODB_USER=\"{get_user_input('MongoDB user', 'mongodb')}\"\n")
            f.write(f"MONGODB_PASSWORD=\"{get_user_input('MongoDB password', 'mongodb')}\"\n")
            f.write(f"MONGODB_DB=\"{get_user_input('MongoDB database', 'fastapi_db')}\"\n")
            f.write(f"MONGODB_SERVICE=\"{get_user_input('MongoDB Docker service name', 'app_mongodb')}\"\n")
            
            # Optional MongoDB connection string
            use_conn_string = get_user_input("Use MongoDB connection string", "false").lower()
            if use_conn_string == "true":
                conn_string = get_user_input("MongoDB connection string", "mongodb://mongodb:mongodb@localhost:27017/fastapi_db")
                f.write(f"MONGODB_CONNECTION_STRING=\"{conn_string}\"\n")
            f.write("\n")
            
            # JWT settings
            f.write("# JWT settings\n")
            f.write(f"JWT_SECRET_KEY=\"{get_user_input('JWT secret key', 'change_this_in_production')}\"\n")
            f.write(f"JWT_ALGORITHM=\"{get_user_input('JWT algorithm', 'HS256')}\"\n")
            f.write(f"JWT_TOKEN_EXPIRE_MINUTES={get_user_input('JWT token expire minutes', '1440')}\n")
            f.write("\n")
            
            # Rate limiting
            f.write("# Rate limiting\n")
            f.write(f"RATE_LIMIT_REQUESTS={get_user_input('Rate limit requests', '100')}\n")
            f.write(f"RATE_LIMIT_TIMEFRAME={get_user_input('Rate limit timeframe (seconds)', '60')}\n")
            f.write("\n")
            
            # Logging
            f.write("# Logging\n")
            f.write(f"LOG_LEVEL=\"{get_user_input('Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)', 'DEBUG')}\"\n")
            f.write("\n")
            
            # Admin user settings
            f.write("# Admin user settings\n")
            f.write(f"ADMIN_EMAIL=\"{get_user_input('Admin email', 'admin@example.com')}\"\n")
            f.write(f"ADMIN_USERNAME=\"{get_user_input('Admin username', 'admin')}\"\n")
            f.write(f"ADMIN_PASSWORD=\"{get_user_input('Admin password', 'admin123')}\"\n")
    
    print("\n.env file created successfully!")
    print("You can now run the application with the configured settings.")


def main():
    """Main function to run the setup script."""
    parser = argparse.ArgumentParser(description="Setup environment for FastAPI Multiple Databases project")
    parser.add_argument("--docker", action="store_true", help="Configure for Docker environment")
    parser.add_argument("--db-type", choices=["postgres", "sqlserver", "mongodb"], default="postgres", 
                        help="Database type to use")
    parser.add_argument("--non-interactive", action="store_true", 
                        help="Use default values without prompting")
    
    args = parser.parse_args()
    
    if args.non_interactive:
        # Create .env file with default values
        with open(".env", "w") as f:
            f.write("# Application settings\n")
            f.write("APP_NAME=\"FastAPI Multiple Databases\"\n")
            f.write("DEBUG=false\n")
            f.write("API_PREFIX=\"/api\"\n\n")
            
            f.write("# Docker settings\n")
            f.write(f"USE_DOCKER={'true' if args.docker else 'false'}\n\n")
            
            f.write("# Primary database settings\n")
            f.write(f"DB_TYPE={args.db_type}\n\n")
            
            f.write("# PostgreSQL settings\n")
            f.write("POSTGRES_HOST=\"localhost\"\n")
            f.write("POSTGRES_PORT=5432\n")
            f.write("POSTGRES_USER=\"postgres\"\n")
            f.write("POSTGRES_PASSWORD=\"postgres\"\n")
            f.write("POSTGRES_DB=\"fastapi_db\"\n")
            f.write("POSTGRES_SERVICE=\"app_postgres\"\n\n")
            
            f.write("# SQL Server settings\n")
            f.write("SQLSERVER_HOST=\"localhost\"\n")
            f.write("SQLSERVER_PORT=1433\n")
            f.write("SQLSERVER_USER=\"sa\"\n")
            f.write("SQLSERVER_PASSWORD=\"YourStrong@Passw0rd\"\n")
            f.write("SQLSERVER_DB=\"fastapi_db\"\n")
            f.write("SQLSERVER_SERVICE=\"app_sqlserver\"\n\n")
            
            f.write("# MongoDB settings\n")
            f.write("MONGODB_HOST=\"localhost\"\n")
            f.write("MONGODB_PORT=27017\n")
            f.write("MONGODB_USER=\"mongodb\"\n")
            f.write("MONGODB_PASSWORD=\"mongodb\"\n")
            f.write("MONGODB_DB=\"fastapi_db\"\n")
            f.write("MONGODB_SERVICE=\"app_mongodb\"\n\n")
            
            f.write("# JWT settings\n")
            f.write("JWT_SECRET_KEY=\"change_this_in_production\"\n")
            f.write("JWT_ALGORITHM=\"HS256\"\n")
            f.write("JWT_TOKEN_EXPIRE_MINUTES=1440\n\n")
            
            f.write("# Rate limiting\n")
            f.write("RATE_LIMIT_REQUESTS=100\n")
            f.write("RATE_LIMIT_TIMEFRAME=60\n\n")
            
            f.write("# Logging\n")
            f.write("LOG_LEVEL=\"DEBUG\"\n\n")
            
            f.write("# Admin user settings\n")
            f.write("ADMIN_EMAIL=\"admin@example.com\"\n")
            f.write("ADMIN_USERNAME=\"admin\"\n")
            f.write("ADMIN_PASSWORD=\"admin123\"\n")
        
        print(".env file created with default values.")
    else:
        # Interactive mode
        print("Setting up environment for FastAPI Multiple Databases project")
        print("Press Enter to accept default values or type your own.")
        create_env_file(use_docker=args.docker, db_type=args.db_type)


if __name__ == "__main__":
    main()
