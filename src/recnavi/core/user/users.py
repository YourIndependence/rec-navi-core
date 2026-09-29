# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""User listing domain logic."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.user import User


async def get_group_users(
    *,
    users_db: BaseDatabase,
    group_id: str,
) -> list[User]:
    """Get all users in a group.

    Queries users table GSI (groupId-index) and automatically fetches
    all pages until LastEvaluatedKey is None.

    Args:
        users_db: Database instance for users table.
        group_id: Group identifier from authenticated user token.

    Returns:
        List of all users in the group (all pages combined).

    """
    all_users: list[User] = []
    last_evaluated_key: dict | None = None

    while True:
        result = await users_db.query(
            key_condition={"groupId": group_id},
            index="groupId-index",
            exclusive_start_key=last_evaluated_key,
        )

        users = [User.model_validate(item) for item in result.items]
        all_users.extend(users)

        last_evaluated_key = result.last_evaluated_key
        if last_evaluated_key is None:
            break

    return all_users
