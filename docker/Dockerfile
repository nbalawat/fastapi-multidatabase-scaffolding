FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv using pip
RUN pip install --no-cache-dir uv

# No need to modify PATH for pip-installed uv

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Copy the application code
COPY . /app/

# Make start script executable
RUN chmod +x /app/start.sh

# Install dependencies using uv with --system flag
RUN uv pip install --system fastapi uvicorn pydantic pydantic-settings python-jose passlib python-multipart sqlalchemy asyncpg aiomysql motor polars httpx tenacity structlog email-validator

# Install development dependencies
RUN uv pip install --system pytest pytest-asyncio pytest-cov black isort mypy ruff

# Install Jupyter Lab
RUN uv pip install --system jupyterlab

# Expose ports for FastAPI and Jupyter Lab
EXPOSE 8000 8888

# Default command will be provided by docker-compose.yml
