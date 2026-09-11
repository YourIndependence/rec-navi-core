# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for core user domain logic."""

import pytest

from recnavi.core.types.user import User
from recnavi.core.user.user import get_user_by_id
from recnavi.exceptions.exceptions import ClientAuthorizationError


class MockUserDatabase:
    """Mock database for testing get_user_by_id."""

    def __init__(self, users: dict[str, dict] | None = None):
        self.users = users or {}

    async def get_item(self, key: dict) -> dict | None:
        user_id = key.get("userId")
        return self.users.get(user_id)

    async def put_item(self, item: dict) -> None:
        pass

    async def query(
        self,
        key_condition: dict,
        filter_expression: dict | None = None,
    ) -> list[dict]:
        return []

    async def delete_item(self, key: dict) -> None:
        pass


@pytest.mark.asyncio
async def test_get_user_by_id_returns_user_when_valid():
    """Test get_user_by_id returns User when data is valid."""
    user_data = {
        "userId": "user-123",
        "userName": "Test User",
        "role": "admin",
        "groupId": "group-456",
    }
    mock_db = MockUserDatabase(users={"user-123": user_data})

    result = await get_user_by_id(user_id="user-123", user_db=mock_db)

    assert isinstance(result, User)
    assert result.user_id == "user-123"
    assert result.user_name == "Test User"
    assert result.role == "admin"
    assert result.group_id == "group-456"


@pytest.mark.asyncio
async def test_get_user_by_id_raises_when_user_not_found():
    """Test get_user_by_id raises ClientAuthorizationError when user not found."""
    mock_db = MockUserDatabase(users={})

    with pytest.raises(
        ClientAuthorizationError,
        match="User not found in database",
    ):
        await get_user_by_id(user_id="nonexistent", user_db=mock_db)


@pytest.mark.asyncio
async def test_get_user_by_id_raises_when_role_invalid():
    """Test get_user_by_id raises ClientAuthorizationError for invalid role."""
    user_data = {
        "userId": "user-789",
        "userName": "Bad Role User",
        "role": "superadmin",
        "groupId": "group-999",
    }
    mock_db = MockUserDatabase(users={"user-789": user_data})

    with pytest.raises(
        ClientAuthorizationError,
        match="Invalid role: superadmin",
    ):
        await get_user_by_id(user_id="user-789", user_db=mock_db)


@pytest.mark.asyncio
async def test_get_user_by_id_accepts_all_valid_roles():
    """Test get_user_by_id accepts admin, owner, and staff roles."""
    for role in ["admin", "owner", "staff"]:
        user_data = {
            "userId": f"user-{role}",
            "userName": f"{role.capitalize()} User",
            "role": role,
            "groupId": "group-123",
        }
        mock_db = MockUserDatabase(users={f"user-{role}": user_data})

        result = await get_user_by_id(user_id=f"user-{role}", user_db=mock_db)

        assert result.role == role
