# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Get group users use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.core.user.users import get_group_users
from recnavi.exceptions.exceptions import ClientAuthorizationError


async def get_group_users_usecase(
    *,
    users_db: BaseDatabase,
    user: User,
) -> list[User]:
    """List members of the authenticated owner's group."""
    if not user.can_act_as(UserRole.OWNER):
        raise ClientAuthorizationError("Only owners can list group users")
    return await get_group_users(users_db=users_db, group_id=user.group_id)
