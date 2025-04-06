# Docker Setup Guide

This guide provides detailed instructions for setting up and running the FastAPI Multiple Databases application using Docker.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)

## Setup Process

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fastapi-scaffolding-multipledatabases
```

### 2. Configure Environment

We provide a setup script specifically for Docker environments:

```bash
python setup_env.py --docker
```

This will create a `.env` file configured for Docker with default values. You can customize these values during the setup process.

Alternatively, you can manually configure the environment:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file and ensure USE_DOCKER=true
```

### 3. Start the Docker Services

```bash
cd docker
docker-compose up
```

This command starts all services defined in the `docker-compose.yml` file, including:

- **PostgreSQL FastAPI Server**: Runs on port 8000 with Jupyter Lab on port 8888
- **MongoDB FastAPI Server**: Runs on port 8001 with Jupyter Lab on port 8889
- **SQL Server FastAPI Server**: Runs on port 8002 with Jupyter Lab on port 8890
- Database services: PostgreSQL, MongoDB, SQL Server, and MySQL

To run a specific service:

```bash
docker-compose up app_postgres  # Only start the PostgreSQL version
```

To run in detached mode:

```bash
docker-compose up -d
```

## Accessing the Services

- **API Documentation**:
  - PostgreSQL version: http://localhost:8000/docs
  - MongoDB version: http://localhost:8001/docs
  - SQL Server version: http://localhost:8002/docs

- **Jupyter Lab**:
  - PostgreSQL version: http://localhost:8888
  - MongoDB version: http://localhost:8889
  - SQL Server version: http://localhost:8890

  Note: You'll need to copy the token from the console output to access Jupyter Lab.

## Docker Configuration

### Environment Variables

The Docker setup uses environment variables from your `.env` file. If a variable isn't defined, it uses a default value.

Key environment variables:

```
# Docker settings
USE_DOCKER=true

# Database selection
DB_TYPE=postgres  # or mongodb, sqlserver

# Service names
POSTGRES_SERVICE=postgres
SQLSERVER_SERVICE=sqlserver
MONGODB_SERVICE=mongodb
```

### Volume Mounts

The application code is mounted as a volume, so changes to the code are immediately reflected without rebuilding the container:

```yaml
volumes:
  - ../:/app
```

### Database Persistence

Database data is persisted using Docker volumes:

```yaml
volumes:
  postgres_data:
  mysql_data:
  mongodb_data:
  sqlserver_data:
```

## Development with Docker

### Running Tests

To run tests inside the Docker container:

```bash
docker-compose exec app_postgres pytest
```

To run tests with coverage:

```bash
docker-compose exec app_postgres pytest --cov=app
```

### Using UV Inside Docker

The Docker setup uses UV for package management. To install new packages:

```bash
docker-compose exec app_postgres uv pip install package-name
```

### Accessing the Shell

To access a shell inside the container:

```bash
docker-compose exec app_postgres /bin/bash
```

## Troubleshooting

### Container Fails to Start

If a container fails to start:

1. Check the logs:
   ```bash
   docker-compose logs app_postgres
   ```

2. Verify that the database services are running:
   ```bash
   docker-compose ps
   ```

3. Check if the ports are already in use on your host machine

### Database Connection Issues

If the application can't connect to the database:

1. Ensure the database service is running
2. Check if the service names in `.env` match those in `docker-compose.yml`
3. Verify that the database credentials are correct

### Rebuilding Containers

If you need to rebuild the containers:

```bash
docker-compose build --no-cache
docker-compose up
```

## Stopping the Services

To stop all services:

```bash
docker-compose down
```

To stop and remove volumes (will delete all data):

```bash
docker-compose down -v
```
