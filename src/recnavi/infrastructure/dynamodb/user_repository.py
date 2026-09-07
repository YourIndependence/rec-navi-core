# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Users stored in DynamoDB."""

import asyncio

from recnavi.core.repositories.user_repository import BaseUserRepository
from recnavi.core.types.group_user import GroupUser
from recnavi.infrastructure.dynamodb.client import get_item


class DynamoDbUserRepository(BaseUserRepository):
    """Users read from the users table."""

    def __init__(self, *, table_name: str) -> None:
        self._table_name = table_name

    async def get(self, *, user_id: str) -> GroupUser | None:
        """Return one user, or nothing when there is no record."""
        item = await asyncio.to_thread(
            get_item,
            self._table_name,
            {"userId": user_id},
        )
        return None if item is None else GroupUser.model_validate(item)
