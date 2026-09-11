# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Core user domain logic."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError


async def get_user_by_id(
    user_database: BaseDatabase,
    user_id: str,
) -> User:
    """Get user from database and validate.

    Args:
        user_id: User ID to fetch.
        user_database: Database instance for user table.

    Returns:
        Validated User object.

    Raises:
        ClientAuthorizationError: If user not found or has invalid role.

    """
    item = await user_database.get_item(key={"userId": user_id})

    if not item:
        raise ClientAuthorizationError("User not found in database")

    role = item.get("role")
    if role not in [r.value for r in UserRole]:
        raise ClientAuthorizationError(f"Invalid role: {role}")

    return User.model_validate(item)
