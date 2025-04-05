# Scripts Directory

This directory contains utility scripts for the FastAPI Multiple Databases application. The scripts are organized into the following categories:

## Directory Structure

```
scripts/
├── db_init/       # Database initialization scripts
├── tests/         # Test scripts for API and functionality
└── utils/         # Utility scripts for maintenance tasks
```

## Database Initialization Scripts (`db_init/`)

Scripts for initializing and setting up databases:

- `create_postgres_db.py` - Creates PostgreSQL database
- `init_admin_sqlserver.py` - Initializes admin user in SQL Server
- `init_db.py` - Generic database initialization
- `init_mongodb.py` - Initializes MongoDB collections
- `init_postgres.py` - Initializes PostgreSQL tables
- `init_sqlserver.py` - Initializes SQL Server database
- `init_tables_postgres.sql` - SQL script for creating tables in PostgreSQL
- `init_tables_sqlserver.sql` - SQL script for creating tables in SQL Server

## Test Scripts (`tests/`)

Scripts for testing the API and functionality:

- `test_generic_api.py` - Tests general API endpoints
- `test_api_mongodb.py` - Tests MongoDB-specific API endpoints
- `test_api_postgres.py` - Tests PostgreSQL-specific API endpoints
- `test_api_sqlserver.py` - Tests SQL Server-specific API endpoints
- `test_integration_mongodb.py` - Tests MongoDB integration
- `test_rbac.py` - Tests Role-Based Access Control system

## Utility Scripts (`utils/`)

Utility scripts for maintenance and administrative tasks:

- `clean_sqlserver_test_db.py` - Cleans SQL Server test database
- `clear_roles.py` - Clears roles from the database

## Usage

Most scripts can be run directly with Python:

```bash
python -m app.scripts.db_init.init_postgres
```

Or from the scripts directory:

```bash
cd app/scripts
python db_init/init_postgres.py
```

## Adding New Scripts

When adding new scripts, please follow these guidelines:

1. Place the script in the appropriate subdirectory based on its purpose
2. Add proper docstrings and type hints
3. Use consistent error handling and logging
4. Update this README with information about the new script
