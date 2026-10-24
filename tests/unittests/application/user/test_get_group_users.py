# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Authorization and tenant isolation for group user listing."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.user.get_group_users import get_group_users_usecase
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.OWNER, UserRole.ADMIN])
async def test_lists_only_authenticated_users_group(role):
    user = User(
        user_id="caller",
        user_name="Caller",
        role=role,
        group_id="group-1",
    )
    database = AsyncMock(spec=BaseDatabase)
    expected_users = [
        User(
            user_id="member",
            user_name="Member",
            role=UserRole.STAFF,
            group_id="group-1",
        ),
    ]
    with patch(
        "recnavi.application.user.get_group_users.get_group_users",
        new=AsyncMock(return_value=expected_users),
    ) as get_users:
        result = await get_group_users_usecase(users_db=database, user=user)
    assert result is expected_users
    get_users.assert_awaited_once_with(
        users_db=database,
        group_id=user.group_id,
    )


@pytest.mark.asyncio
async def test_staff_is_rejected_before_database_access():
    database = AsyncMock(spec=BaseDatabase)
    user = User(
        user_id="staff",
        user_name="Staff",
        role=UserRole.STAFF,
        group_id="group-1",
    )
    with pytest.raises(ClientAuthorizationError):
        await get_group_users_usecase(users_db=database, user=user)
    database.query.assert_not_awaited()
