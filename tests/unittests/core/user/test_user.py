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
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_user_by_id_returns_user_when_valid():
    """Test get_user_by_id returns User when data is valid."""
    user_data = {
        "userId": "user-123",
        "userName": "Test User",
        "role": "admin",
        "groupId": "group-456",
        "email": "test@example.com",
        "phoneNumber": "090-1234-5678",
        "birthday": "1990-01-01",
        "profileImageUri": "s3://bucket/user-123/profile.jpg",
    }
    mock_db = MockDatabase(initial_items=[user_data])

    result = await get_user_by_id(user_id="user-123", user_database=mock_db)

    assert isinstance(result, User)
    assert result.user_id == "user-123"
    assert result.user_name == "Test User"
    assert result.role == "admin"
    assert result.group_id == "group-456"
    assert result.email == "test@example.com"
    assert result.phone_number == "090-1234-5678"
    assert result.birthday == "1990-01-01"
    assert result.profile_image_uri == "s3://bucket/user-123/profile.jpg"


@pytest.mark.asyncio
async def test_get_user_by_id_raises_when_user_not_found():
    """Test get_user_by_id raises ClientAuthorizationError when user not found."""
    mock_db = MockDatabase()

    with pytest.raises(
        ClientAuthorizationError,
        match="User not found in database",
    ):
        await get_user_by_id(user_id="nonexistent", user_database=mock_db)


@pytest.mark.asyncio
async def test_get_user_by_id_raises_when_role_invalid():
    """Test get_user_by_id raises ClientAuthorizationError for invalid role."""
    user_data = {
        "userId": "user-789",
        "userName": "Bad Role User",
        "role": "superadmin",
        "groupId": "it-group",
        "email": "bad@example.com",
        "phoneNumber": "090-9999-9999",
        "birthday": "1985-05-05",
        "profileImageUri": "s3://bucket/user-789/profile.jpg",
    }
    mock_db = MockDatabase(initial_items=[user_data])

    with pytest.raises(
        ClientAuthorizationError,
        match="Invalid role: superadmin",
    ):
        await get_user_by_id(user_id="user-789", user_database=mock_db)


@pytest.mark.asyncio
async def test_get_user_by_id_accepts_all_valid_roles():
    """Test get_user_by_id accepts admin, owner, and staff roles."""
    for role in ["admin", "owner", "staff"]:
        user_data = {
            "userId": f"user-{role}",
            "userName": f"{role.capitalize()} User",
            "role": role,
            "groupId": "group-123",
            "email": f"{role}@example.com",
            "phoneNumber": "090-0000-0000",
            "birthday": "2000-01-01",
            "profileImageUri": f"s3://bucket/user-{role}/profile.jpg",
        }
        mock_db = MockDatabase(initial_items=[user_data])

        result = await get_user_by_id(
            user_id=f"user-{role}",
            user_database=mock_db,
        )

        assert result.role == role
