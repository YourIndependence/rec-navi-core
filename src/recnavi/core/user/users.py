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
    """Get the active users in a group (auto-paginated from groupId-index GSI).

    Deactivated users are skipped here but their records are kept, so
    references such as a scene's createdBy still resolve. Records without
    an isActive attribute count as active.
    """
    all_users: list[User] = []
    last_evaluated_key = None

    while True:
        result = await users_db.query(
            key_condition={"groupId": group_id},
            index="groupId-index",
            exclusive_start_key=last_evaluated_key,
        )

        users = [User.model_validate(item) for item in result.items]
        all_users.extend(user for user in users if user.is_active)

        last_evaluated_key = result.last_evaluated_key
        if not last_evaluated_key:
            break

    return all_users
