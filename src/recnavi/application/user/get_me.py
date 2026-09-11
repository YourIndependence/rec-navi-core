# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Get current authenticated user use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError


async def get_me_use_case(sub: str, user_db: BaseDatabase) -> User:
    """Get current authenticated user by Cognito sub.

    This use case retrieves the user from the users table using the Cognito
    sub (subject) claim from the verified JWT token. The user's role and
    group membership are stored in DynamoDB, not in Cognito, so that changes
    take effect immediately without requiring the user to re-authenticate.

    Args:
        sub: Cognito user sub (subject identifier from JWT token).
        user_db: Database instance for accessing users table.

    Returns:
        User object with userId, userName, role, and groupId.

    Raises:
        ClientAuthorizationError: User not found in database (403).
        ClientAuthorizationError: User has invalid or unknown role (403).

    """
    item = await user_db.get_item(key={"userId": sub})

    if not item:
        raise ClientAuthorizationError("User not found in database")

    role = item.get("role")
    if role not in [r.value for r in UserRole]:
        raise ClientAuthorizationError(f"Invalid role: {role}")

    return User.model_validate(item)
