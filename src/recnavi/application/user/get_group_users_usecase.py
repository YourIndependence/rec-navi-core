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
from recnavi.core.user.users import get_group_users


async def get_group_users_usecase(
    *,
    users_db: BaseDatabase,
    group_id: str,
) -> list[User]:
    """Get all users in a group.

    Args:
        users_db: Database instance for users table.
        group_id: Group identifier from authenticated user token.

    Returns:
        List of all users in the group.

    """
    return await get_group_users(users_db=users_db, group_id=group_id)
