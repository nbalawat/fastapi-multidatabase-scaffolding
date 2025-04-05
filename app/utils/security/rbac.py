# This module is deprecated and will be removed in a future version
# All functionality has been moved to app.core.security

import logging
from typing import List, Dict, Any

# Import all functionality from core security module
from app.core.security import (
    RBACMiddleware,
    create_rbac_routes,
    decode_token,
    get_current_user,
    oauth2_scheme
)

logger = logging.getLogger(__name__)
logger.warning(
    "app.utils.security.rbac is deprecated and will be removed in a future version. "
    "Please use app.core.security instead."
)

# RBACMiddleware class is now imported from app.core.security

# create_rbac_routes function is now imported from app.core.security
