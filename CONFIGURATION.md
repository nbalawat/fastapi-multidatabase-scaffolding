# Configuration Guide

This guide explains how to configure the FastAPI Multiple Databases application for different environments, including both Docker and non-Docker setups.

## Environment Configuration

The application uses environment variables for configuration, which can be set in a `.env` file or directly in your system environment.

### Setting Up Your Environment

We provide two ways to set up your environment:

1. **Interactive Setup Script** (Recommended for new users):
   ```bash
   python setup_env.py
   ```
   This script will guide you through setting up your environment with interactive prompts.

2. **Manual Setup**:
   - Copy `.env.example` to `.env`
   - Edit the `.env` file to match your environment

### Command-line Options for Setup Script

The setup script supports several command-line options:

```bash
# Set up for Docker environment
python setup_env.py --docker

# Set up for a specific database type
python setup_env.py --db-type mongodb

# Use default values without prompts
python setup_env.py --non-interactive
```

## Docker vs Non-Docker Configuration

The application supports both Docker and non-Docker environments:

### Docker Environment

When running with Docker:
- Set `USE_DOCKER=true` in your `.env` file
- The application will use service names (like `app_postgres`) to connect to databases
- Database services are defined in `docker-compose.yml`

### Non-Docker Environment

When running without Docker:
- Set `USE_DOCKER=false` in your `.env` file
- The application will use hostnames (like `localhost`) to connect to databases
- You need to ensure your databases are running and accessible

## Database Configuration

The application supports multiple database types:

### PostgreSQL Configuration

```
DB_TYPE=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fastapi_db
```

### SQL Server Configuration

```
DB_TYPE=sqlserver
SQLSERVER_HOST=localhost
SQLSERVER_PORT=1433
SQLSERVER_USER=sa
SQLSERVER_PASSWORD=YourStrong@Passw0rd
SQLSERVER_DB=fastapi_db
```

### MongoDB Configuration

```
DB_TYPE=mongodb
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=mongodb
MONGODB_PASSWORD=mongodb
MONGODB_DB=fastapi_db
# Optional: Use connection string instead of individual parameters
# MONGODB_CONNECTION_STRING=mongodb://mongodb:mongodb@localhost:27017/fastapi_db
```

## Package Management

The project supports both UV and pip for package management:

### Using UV (Recommended)

UV is a fast, reliable Python package installer and resolver. To use UV:

```bash
# Install dependencies
uv pip sync

# Add a new dependency
uv pip install package-name
```

### Using pip

If you're not familiar with UV, you can use standard pip:

```bash
# Install dependencies
pip install -r requirements.txt

# Add a new dependency
pip install package-name
```

## Additional Configuration

### JWT Settings

```
JWT_SECRET_KEY=change_this_in_production
JWT_ALGORITHM=HS256
JWT_TOKEN_EXPIRE_MINUTES=1440
```

### Rate Limiting

```
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_TIMEFRAME=60
```

### Logging

```
LOG_LEVEL=DEBUG
```

### Admin User

```
ADMIN_EMAIL=admin@example.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

## How Configuration Works

The application uses Pydantic's `BaseSettings` to load and validate configuration:

1. Environment variables are loaded from the `.env` file
2. System environment variables override `.env` file values
3. The `Settings` class validates and processes the configuration
4. Database connection parameters are automatically set based on the selected database type

This approach ensures that configuration is flexible, type-safe, and works in various environments.
