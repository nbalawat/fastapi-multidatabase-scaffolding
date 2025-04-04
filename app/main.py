from fastapi import FastAPI, Depends
from functools import lru_cache

from app.core.config import get_settings, Settings
from app.db.base import DatabaseAdapter, DatabaseAdapterFactory

# Import all database adapters to register them with the factory
from app.db.postgres.adapter import PostgresAdapter
from app.db.mysql.adapter import MySQLAdapter
from app.db.mongodb.adapter import MongoDBAdapter

# Create the FastAPI application
app = FastAPI(
    title=get_settings().app_name,
    description="FastAPI server with multiple database support",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


@lru_cache
def get_db_adapter() -> DatabaseAdapter:
    """Get the appropriate database adapter based on configuration.
    
    Returns:
        An instance of the configured database adapter
    """
    settings = get_settings()
    return DatabaseAdapterFactory.get_adapter(settings.db_type)


@app.get("/")
async def read_root():
    """Root endpoint providing basic application information."""
    settings = get_settings()
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "description": "FastAPI server with multiple database support"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}


# Include API routers
from app.api.routes import auth, users
app.include_router(auth.router, prefix=get_settings().api_prefix)
app.include_router(users.router, prefix=get_settings().api_prefix)


@app.on_event("startup")
async def startup_event():
    """Initialize resources when the application starts."""
    # Connect to the database
    adapter = get_db_adapter()
    await adapter.connect()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the application shuts down."""
    # Disconnect from the database
    adapter = get_db_adapter()
    await adapter.disconnect()
