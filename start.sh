#!/bin/bash
set -e

# Initialize environment
echo "Setting up environment..."

# Wait for databases to be ready
echo "Waiting for databases to be ready..."

# Function to check if MongoDB is ready
wait_for_mongodb() {
    echo "Waiting for MongoDB to be ready..."
    max_retries=30
    retries=0
    
    while [ $retries -lt $max_retries ]; do
        if mongosh --host $DB_HOST --port $DB_PORT -u $DB_USER -p $DB_PASSWORD --authenticationDatabase admin --eval "db.adminCommand('ping')" &>/dev/null; then
            echo "MongoDB is ready!"
            return 0
        fi
        
        echo "MongoDB not ready yet. Retrying in 2 seconds..."
        sleep 2
        retries=$((retries + 1))
    done
    
    echo "Timed out waiting for MongoDB to be ready"
    return 1
}

# Function to check if SQL Server is ready
wait_for_sqlserver() {
    echo "Waiting for SQL Server to be ready..."
    max_retries=60
    retries=0
    
    while [ $retries -lt $max_retries ]; do
        if /opt/mssql-tools18/bin/sqlcmd -S $SQLSERVER_HOST,$SQLSERVER_PORT -U $SQLSERVER_USER -P $SQLSERVER_PASSWORD -Q "SELECT 1" &>/dev/null; then
            echo "SQL Server is ready!"
            return 0
        fi
        
        echo "SQL Server not ready yet. Retrying in 5 seconds..."
        sleep 5
        retries=$((retries + 1))
    done
    
    echo "Timed out waiting for SQL Server to be ready"
    return 1
}

# Wait for the appropriate database based on DB_TYPE
if [ "$DB_TYPE" = "mongodb" ]; then
    # Install mongosh if not available
    if ! command -v mongosh &> /dev/null; then
        echo "Installing MongoDB Shell..."
        apt-get update && apt-get install -y wget gnupg
        wget -qO- https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list
        apt-get update && apt-get install -y mongodb-mongosh
    fi
    
    wait_for_mongodb || echo "Proceeding anyway..."
elif [ "$DB_TYPE" = "sqlserver" ]; then
    # Check if SQL Server tools are available
    if [ ! -f /opt/mssql-tools18/bin/sqlcmd ]; then
        echo "SQL Server tools not found. Make sure msodbcsql18 is installed."
    else
        wait_for_sqlserver || echo "Proceeding anyway..."
    fi
else
    # Simple wait for other database types
    echo "Using simple wait for non-MongoDB/SQL Server database..."
    sleep 5
fi

# Initialize databases
echo "Initializing databases..."

# First, ensure all adapters are registered by importing the main module
python -c "from app.main import app; print('Database adapters registered successfully')" || echo "Failed to register database adapters"

# Initialize databases using the new schema registry and admin initializer
echo "Initializing databases using schema registry..."

# The database initialization is now handled by the application startup
# through the lifespan context manager in app.main.py
# This includes:
# 1. Schema registry initialization
# 2. Database schema creation
# 3. Admin user initialization

# Skip manual database initialization - the application will handle this during startup
echo "Database initialization will be handled during application startup through the lifespan context manager."

# Start application based on command
if [ "$1" = "jupyter" ]; then
    echo "Starting Jupyter Lab..."
    jupyter lab --ip=0.0.0.0 --allow-root --no-browser
else
    echo "Starting FastAPI application..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
