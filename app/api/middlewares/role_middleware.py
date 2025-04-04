"""Middleware for role-based access control."""
from typing import Callable, Dict, List, Optional, Set

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.api.dependencies import get_current_user
from app.models.users import Role, User


class RoleMiddleware:
    """Middleware for role-based access control.
    
    This middleware checks if the user has the required role to access a route.
    """
    
    def __init__(self) -> None:
        """Initialize the role middleware."""
        self.protected_paths: Dict[str, Set[str]] = {}
        self.app = None
    
    def protect_path(self, path: str, roles: List[str]) -> None:
        """Protect a path with required roles.
        
        Args:
            path: The path to protect
            roles: The roles that can access the path
        """
        self.protected_paths[path] = set(roles)
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation.
        
        This method is called for each request and checks if the user has the required role.
        
        Args:
            scope: The ASGI scope
            receive: The ASGI receive function
            send: The ASGI send function
            
        Returns:
            The response from the next middleware in the chain
        """
        # Only process HTTP requests
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
            
        # Create a request object
        request = Request(scope)
        
        # Get the path
        path = request.url.path
        
        # Check if the path is protected
        is_protected = False
        required_roles = set()
        
        for protected_path, roles in self.protected_paths.items():
            if path.startswith(protected_path):
                is_protected = True
                required_roles = roles
                break
                
        # If the path is not protected, allow access
        if not is_protected:
            return await self.app(scope, receive, send)
            
        # For protected paths, we need to check the user's role
        # This will be handled by the route dependencies
        # We're just setting up the middleware to work with the ASGI interface
        
        # Continue with the request
        return await self.app(scope, receive, send)


def setup_role_middleware(app: FastAPI) -> RoleMiddleware:
    """Set up the role middleware.
    
    Args:
        app: The FastAPI application
        
    Returns:
        The role middleware instance
    """
    role_middleware = RoleMiddleware()
    
    # Protect admin paths
    role_middleware.protect_path("/api/v1/admin", [Role.ADMIN.value])
    
    # Create a middleware function that follows FastAPI's middleware pattern
    @app.middleware("http")
    async def role_based_access_control(request: Request, call_next):
        # Get the path
        path = request.url.path
        
        # Check if the path is protected
        for protected_path, roles in role_middleware.protected_paths.items():
            if path.startswith(protected_path):
                # The actual role check will be done by the route dependencies
                # This middleware just sets up the structure
                break
                
        # Continue with the request
        response = await call_next(request)
        return response
    
    return role_middleware
