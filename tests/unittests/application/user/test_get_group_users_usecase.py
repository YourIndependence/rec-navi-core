# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for get_group_users_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.user.get_group_users_usecase import (
    get_group_users_usecase,
)
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_usecase_delegates_to_get_group_users():
    """Test usecase delegates to core get_group_users collaborator."""
    mock_db = AsyncMock()
    expected_users = [
        User(
            user_id="user-1",
            user_name="Alice",
            group_id="group-1",
            role=UserRole.OWNER,
        ),
        User(
            user_id="user-2",
            user_name="Bob",
            group_id="group-1",
            role=UserRole.STAFF,
        ),
    ]

    with patch(
        "recnavi.application.user.get_group_users_usecase.get_group_users",
        new=AsyncMock(return_value=expected_users),
    ) as mock_get:
        result = await get_group_users_usecase(
            users_db=mock_db,
            group_id="group-1",
        )

    mock_get.assert_awaited_once_with(users_db=mock_db, group_id="group-1")
    assert result is expected_users


@pytest.mark.asyncio
async def test_get_group_users_usecase_returns_all_users():
    """Test usecase returns all users in a group."""
    database = MockDatabase(
        initial_items=[
            {
                "userId": "user-1",
                "userName": "Alice",
                "role": "owner",
                "groupId": "group-1",
            },
            {
                "userId": "user-2",
                "userName": "Bob",
                "role": "staff",
                "groupId": "group-1",
            },
        ],
    )

    users = await get_group_users_usecase(
        users_db=database,
        group_id="group-1",
    )

    assert len(users) == 2
    assert users[0].user_id == "user-1"
    assert users[1].user_id == "user-2"


@pytest.mark.asyncio
async def test_get_group_users_usecase_calls_core_layer():
    """Test usecase delegates to core layer get_group_users."""
    database = MockDatabase(
        initial_items=[
            {
                "userId": "user-123",
                "userName": "Test User",
                "role": "admin",
                "groupId": "group-abc",
            },
        ],
    )

    users = await get_group_users_usecase(
        users_db=database,
        group_id="group-abc",
    )

    assert len(users) == 1
    assert users[0].user_id == "user-123"
    assert users[0].user_name == "Test User"
    assert users[0].role == UserRole.ADMIN
    assert users[0].group_id == "group-abc"
