# This module is deprecated and will be removed in a future version
# All functionality has been moved to app.core.security

import logging

# Import all functionality from core security module for backward compatibility
from app.core.security import (
    RBACMiddleware,
    create_rbac_routes,
    decode_token,
    get_current_user,
    oauth2_scheme,
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    has_role
)

logger = logging.getLogger(__name__)
logger.warning(
    "app.utils.security is deprecated and will be removed in a future version. "
    "Please use app.core.security instead."
)
