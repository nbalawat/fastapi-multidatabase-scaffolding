from fastapi import FastAPI, Depends, HTTPException, status

from app.core.config import get_settings, Settings
from app.db.base import DatabaseAdapter
from app.api.dependencies import get_db_adapter

# Import all database adapters to register them with the factory
from app.db.postgres.adapter import PostgresAdapter
from app.db.mysql.adapter import MySQLAdapter
from app.db.mongodb.adapter import MongoDBAdapter
from app.db.sqlserver.adapter import SQLServerAdapter

# Create the FastAPI application
app = FastAPI(
    title=get_settings().app_name,
    description="FastAPI server with multiple database support",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
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


# Include API routers
from app.api.routes import auth, users, notes, roles
from app.api.middlewares.role_middleware import setup_role_middleware

# Set up role-based middleware
role_middleware = setup_role_middleware(app)

# Include routers
app.include_router(auth.router, prefix=get_settings().api_prefix)
app.include_router(users.router, prefix=get_settings().api_prefix)
app.include_router(notes.router, prefix=f"{get_settings().api_prefix}/notes")
app.include_router(roles.router, prefix=f"{get_settings().api_prefix}/roles")


# Use on_event handlers for compatibility with older FastAPI versions
@app.on_event("startup")
async def startup_event():
    """Initialize resources when the application starts.
    
    Database connections are now handled by the dependency injection system.
    """
    # No need to manually connect to the database
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the application shuts down.
    
    Database disconnections are now handled by the dependency injection system.
    """
    # No need to manually disconnect from the database
    pass
