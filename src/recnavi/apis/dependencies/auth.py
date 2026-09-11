# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Authentication dependencies for FastAPI."""

from fastapi import Request

from recnavi.apis.auth.auth import decode_token
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.types.user import User
from recnavi.core.user.user import get_user_by_id


async def verify_user(request: Request) -> User:
    """Verify JWT token and return authenticated user from database.

    This dependency can be used in any endpoint to get the current user:
    ```python
    @router.get("/example")
    async def example(user: User = Depends(verify_user)):
        # user is already verified and fetched from database
        print(user.user_id, user.role, user.group_id)
    ```

    Args:
        request: FastAPI request object.

    Returns:
        User object with userId, userName, role, and groupId.

    Raises:
        ClientPermissionError (401): Token missing, invalid, or expired.
        ClientAuthorizationError (403): Valid token but user not in database,
            or user has invalid role.

    """
    payload = await decode_token(request)
    sub = str(payload["sub"])

    user_db = request.app.state.database[USERS_TABLE_NAME]
    user = await get_user_by_id(user_id=sub, user_db=user_db)

    return user
