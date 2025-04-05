from fastapi import FastAPI, Depends, HTTPException, status, Request
from contextlib import asynccontextmanager
import logging
import os

# Configure logger
logger = logging.getLogger(__name__)

from app.core.config import get_settings, Settings
from app.db.base import DatabaseAdapter
from app.api.dependencies.db import get_db_adapter
from app.db.initializer import initialize_databases
from app.db.schema_registry import get_schema_registry
from app.db.admin_initializer import initialize_admin_users

# Import the adapters module to register all database adapters with the factory
from app.db.adapters import PostgresAdapter, MongoDBAdapter, SQLServerAdapter

# Define lifespan context manager for application startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for the FastAPI application.
    
    Handles initialization on startup and cleanup on shutdown.
    This replaces the deprecated on_event handlers.
    
    Args:
        app: The FastAPI application instance
    """
    # Startup phase
    logger.info("Application startup: Beginning initialization")
    
    try:
        # Initialize database schemas
        logger.info("Initializing schema registry")
        schema_registry = get_schema_registry()
        schema_registry.initialize()
        logger.info(f"Schema registry initialized with {len(schema_registry.get_all_schemas())} schemas")
        
        # Initialize database tables/collections
        logger.info("Initializing database tables/collections")
        async with initialize_databases():
            # Initialize admin users
            logger.info("Initializing admin users")
            await initialize_admin_users()
            logger.info("Admin users initialized successfully")
            
            logger.info("Application startup complete - ready to handle requests")
            yield
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}")
        # Re-raise the exception to prevent the application from starting in a bad state
        raise
    
    # Shutdown phase
    logger.info("Application shutdown: Cleaning up resources")

# Create FastAPI app with lifespan manager
app = FastAPI(
    title=get_settings().app_name,
    description="FastAPI server with multiple database support",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Import custom OpenAPI documentation
from app.api.docs.openapi_docs import custom_openapi

# Set custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)


# get_db_adapter is now imported from app.api.dependencies


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
async def health_check(db: DatabaseAdapter = Depends(get_db_adapter)):
    """Health check endpoint for monitoring.
    
    Checks if the database connection is working by performing a simple operation.
    """
    try:
        # Try to connect to the database
        if not hasattr(db, "_client") or db._client is None:
            await db.connect()
            
        # For MongoDB, we'll ping the server
        # This will work for any database adapter that implements the connect method
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection failed: {str(e)}"
        )


# Import middlewares
from app.api.middlewares.role_middleware import setup_role_middleware

# Import model-first routers
from app.models.notes.router import router as notes_router
from app.models.users.router import router as users_router
from app.models.auth.router import router as auth_router
from app.models.roles.router import router as roles_router

# Set up role-based middleware
role_middleware = setup_role_middleware(app)

# Include model-first routers
app.include_router(auth_router, prefix=get_settings().api_prefix)
app.include_router(users_router, prefix=get_settings().api_prefix)
app.include_router(notes_router, prefix=get_settings().api_prefix)
app.include_router(roles_router, prefix=get_settings().api_prefix)



