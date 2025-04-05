from fastapi import APIRouter

from app.models.notes.router import router as notes_router
from app.models.users.router import router as users_router

# Create main API router
api_router = APIRouter()

# Include model-specific routers
api_router.include_router(notes_router)
api_router.include_router(users_router)
