# Local Setup Guide

This guide explains how to set up and run the FastAPI Multiple Databases application in your local environment, with or without Docker.

## Prerequisites

- Python 3.9+ installed
- [UV](https://docs.astral.sh/uv/) installed (recommended) or pip
- Docker and Docker Compose (optional, for Docker setup)
- Access to PostgreSQL, SQL Server, or MongoDB (if not using Docker)

## Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fastapi-scaffolding-multipledatabases
```

### 2. Configure Environment

We provide a setup script that helps you configure your environment:

```bash
python setup_env.py
```

This interactive script will guide you through setting up your `.env` file with the appropriate configuration.

Alternatively, you can:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your preferred settings
```

## Running Without Docker

If you prefer to run the application without Docker, follow these steps:

### 1. Install Dependencies

Using UV (recommended):

```bash
uv pip sync
```

Using pip:

```bash
pip install -e .
```

### 2. Configure Local Databases

Ensure your `.env` file has `USE_DOCKER=false` and configure the connection parameters for your database:

For PostgreSQL:
```
DB_TYPE=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fastapi_db
```

For SQL Server:
```
DB_TYPE=sqlserver
SQLSERVER_HOST=localhost
SQLSERVER_PORT=1433
SQLSERVER_USER=sa
SQLSERVER_PASSWORD=YourStrong@Passw0rd
SQLSERVER_DB=fastapi_db
```

For MongoDB:
```
DB_TYPE=mongodb
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=mongodb
MONGODB_PASSWORD=mongodb
MONGODB_DB=fastapi_db
```

### 3. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000.

## Running With Docker

If you prefer to use Docker, follow these steps:

### 1. Configure Environment for Docker

Ensure your `.env` file has `USE_DOCKER=true`. You can use the setup script with the `--docker` flag:

```bash
python setup_env.py --docker
```

### 2. Start the Docker Services

```bash
cd docker
docker-compose up
```

This will start:
- The FastAPI application with PostgreSQL database at http://localhost:8000
- The FastAPI application with MongoDB database at http://localhost:8001
- The FastAPI application with SQL Server database at http://localhost:8002
- Jupyter Lab at http://localhost:8888 (for PostgreSQL), http://localhost:8889 (for MongoDB), and http://localhost:8890 (for SQL Server)

### 3. Access the Services

- API Documentation: http://localhost:8000/docs
- Jupyter Lab: http://localhost:8888 (enter the token from the console output)

## Development Workflow

### Running Tests

We use pytest for testing:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app
```

### Adding New Features

Follow the test-driven development process:

1. Write tests for the new feature
2. Implement the feature
3. Run tests to ensure they pass
4. Push changes to git when the feature is complete

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

1. Verify your `.env` file has the correct connection parameters
2. Check if the database service is running
3. For Docker, ensure the service names match those in `docker-compose.yml`
4. For non-Docker, ensure the hostnames and ports are correct

### Permission Issues

If you encounter permission issues with the API:

1. Verify that the admin user is created correctly
2. Check if the token has the correct roles and permissions
3. Ensure the endpoint has the correct permission requirements

## Additional Resources

- [Configuration Guide](../CONFIGURATION.md) - Detailed information about configuration options
- [API Documentation](http://localhost:8000/docs) - Interactive API documentation (when the server is running)
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Official FastAPI documentation
