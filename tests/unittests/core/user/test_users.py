# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for user listing domain logic."""

import pytest

from recnavi.core.types.user import UserRole
from recnavi.core.user.users import get_group_users
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_group_users_returns_all_users_in_group():
    """Test get_group_users returns all users in a group."""
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
            {
                "userId": "user-3",
                "userName": "Charlie",
                "role": "admin",
                "groupId": "group-1",
            },
        ],
    )

    users = await get_group_users(users_db=database, group_id="group-1")

    assert len(users) == 3
    user_ids = {u.user_id for u in users}
    assert user_ids == {"user-1", "user-2", "user-3"}


@pytest.mark.asyncio
async def test_get_group_users_handles_pagination():
    """Test get_group_users handles pagination (2+ pages)."""
    items = [
        {
            "userId": f"user-{i}",
            "userName": f"User {i}",
            "role": "staff",
            "groupId": "group-big",
        }
        for i in range(120)
    ]
    database = MockDatabase(initial_items=items)

    users = await get_group_users(users_db=database, group_id="group-big")

    assert len(users) == 120


@pytest.mark.asyncio
async def test_get_group_users_excludes_other_groups():
    """Test get_group_users excludes users from other groups."""
    database = MockDatabase(
        initial_items=[
            {
                "userId": "user-a",
                "userName": "Alice",
                "role": "owner",
                "groupId": "group-a",
            },
            {
                "userId": "user-b",
                "userName": "Bob",
                "role": "staff",
                "groupId": "group-b",
            },
        ],
    )

    users = await get_group_users(users_db=database, group_id="group-a")

    assert len(users) == 1
    assert users[0].user_id == "user-a"


@pytest.mark.asyncio
async def test_get_group_users_returns_empty_for_empty_group():
    """Test get_group_users returns empty list for group with no users."""
    database = MockDatabase(initial_items=[])

    users = await get_group_users(users_db=database, group_id="group-empty")

    assert users == []


@pytest.mark.asyncio
async def test_get_group_users_preserves_user_fields():
    """Test get_group_users preserves userId, userName, role fields."""
    database = MockDatabase(
        initial_items=[
            {
                "userId": "user-123",
                "userName": "Test User",
                "role": "staff",
                "groupId": "group-1",
            },
        ],
    )

    users = await get_group_users(users_db=database, group_id="group-1")

    assert len(users) == 1
    user = users[0]
    assert user.user_id == "user-123"
    assert user.user_name == "Test User"
    assert user.role == UserRole.STAFF
    assert user.group_id == "group-1"


@pytest.mark.asyncio
async def test_get_group_users_includes_all_roles():
    """Test get_group_users includes admin, owner, and staff roles."""
    database = MockDatabase(
        initial_items=[
            {
                "userId": "admin-1",
                "userName": "Admin",
                "role": "admin",
                "groupId": "group-1",
            },
            {
                "userId": "owner-1",
                "userName": "Owner",
                "role": "owner",
                "groupId": "group-1",
            },
            {
                "userId": "staff-1",
                "userName": "Staff",
                "role": "staff",
                "groupId": "group-1",
            },
        ],
    )

    users = await get_group_users(users_db=database, group_id="group-1")

    roles = {u.role for u in users}
    assert roles == {UserRole.ADMIN, UserRole.OWNER, UserRole.STAFF}
