# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_me_use_case."""

import pytest

from recnavi.application.user.get_me import get_me_use_case
from recnavi.core.types.user import User
from recnavi.exceptions.exceptions import ClientAuthorizationError


class FakeUserDatabase:
    """Fake database for testing get_me_use_case."""

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
async def test_get_me_returns_user_when_valid():
    """Test get_me_use_case returns User when data is valid."""
    user_data = {
        "userId": "user-123",
        "userName": "Test User",
        "role": "admin",
        "groupId": "group-456",
    }
    fake_db = FakeUserDatabase(users={"user-123": user_data})

    result = await get_me_use_case(sub="user-123", user_db=fake_db)

    assert isinstance(result, User)
    assert result.user_id == "user-123"
    assert result.user_name == "Test User"
    assert result.role == "admin"
    assert result.group_id == "group-456"


@pytest.mark.asyncio
async def test_get_me_raises_when_user_not_found():
    """Test get_me_use_case raises ClientAuthorizationError when user not found."""
    fake_db = FakeUserDatabase(users={})

    with pytest.raises(
        ClientAuthorizationError,
        match="User not found in database",
    ):
        await get_me_use_case(sub="nonexistent", user_db=fake_db)


@pytest.mark.asyncio
async def test_get_me_raises_when_role_invalid():
    """Test get_me_use_case raises ClientAuthorizationError for invalid role."""
    user_data = {
        "userId": "user-789",
        "userName": "Bad Role User",
        "role": "superadmin",
        "groupId": "group-999",
    }
    fake_db = FakeUserDatabase(users={"user-789": user_data})

    with pytest.raises(
        ClientAuthorizationError,
        match="Invalid role: superadmin",
    ):
        await get_me_use_case(sub="user-789", user_db=fake_db)


@pytest.mark.asyncio
async def test_get_me_accepts_all_valid_roles():
    """Test get_me_use_case accepts admin, owner, and staff roles."""
    for role in ["admin", "owner", "staff"]:
        user_data = {
            "userId": f"user-{role}",
            "userName": f"{role.capitalize()} User",
            "role": role,
            "groupId": "group-123",
        }
        fake_db = FakeUserDatabase(users={f"user-{role}": user_data})

        result = await get_me_use_case(sub=f"user-{role}", user_db=fake_db)

        assert result.role == role
