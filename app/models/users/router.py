from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import logging

from app.models.users.model import UserCreate, UserUpdate, User
from app.models.users.controller import UsersController
from app.api.dependencies.db import get_db_adapter
from app.utils.generic.router_utils import create_standard_routes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

# Create standard CRUD routes
create_standard_routes(
    router=router,
    controller_class=UsersController,
    create_model=UserCreate,
    update_model=UserUpdate,
    response_model=User,
    get_db_adapter=get_db_adapter
)

# Add custom routes
@router.post("/login")
async def login(username: str, password: str, db_adapter=Depends(get_db_adapter)):
    """Authenticate a user."""
    controller = UsersController(db_adapter)
    user = await controller.authenticate(username, password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return {"access_token": f"dummy_token_{username}", "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(username: str, db_adapter=Depends(get_db_adapter)):
    """Get current user."""
    controller = UsersController(db_adapter)
    users = await controller.list(0, 1, {"username": username})
    
    if not users:
        raise HTTPException(status_code=404, detail="User not found")
        
    return users[0]
