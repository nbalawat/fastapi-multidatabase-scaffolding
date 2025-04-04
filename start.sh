#!/bin/bash
set -e

# Initialize environment
echo "Setting up environment..."

# Wait for databases to be ready
echo "Waiting for databases to be ready..."
sleep 5  # Simple wait to ensure databases are up

# Initialize databases
echo "Initializing databases..."

# First, ensure all adapters are registered by importing the main module
python -c "from app.main import app; print('Database adapters registered successfully')" || echo "Failed to register database adapters"

# Create the PostgreSQL database if it doesn't exist
echo "Creating PostgreSQL database if it doesn't exist..."
python -m app.scripts.create_postgres_db

# Initialize PostgreSQL tables
python -m app.scripts.init_postgres  # Initialize PostgreSQL tables

# Create admin user
python -m app.scripts.init_db  # Create admin user

# Start application based on command
if [ "$1" = "jupyter" ]; then
    echo "Starting Jupyter Lab..."
    jupyter lab --ip=0.0.0.0 --allow-root --no-browser
else
    echo "Starting FastAPI application..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
