# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Get current user use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.user import User
from recnavi.core.user.user import get_user_by_id


async def get_me_use_case(sub: str, user_db: BaseDatabase) -> User:
    """Get current authenticated user.

    Application layer orchestration: simply calls core domain logic.

    Args:
        sub: User ID from authentication token.
        user_db: Database instance for users table.

    Returns:
        User object.

    Raises:
        ClientAuthorizationError: If user not found or invalid.

    """
    return await get_user_by_id(user_id=sub, user_db=user_db)
