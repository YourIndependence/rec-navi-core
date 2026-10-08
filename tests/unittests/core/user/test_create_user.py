# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for create_user core logic."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.core.user.create_user import create_user
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientValueError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_identity_provider import MockIdentityProvider


def _caller(role: UserRole = UserRole.OWNER) -> User:
    return User(
        user_id="owner-1",
        user_name="Owner",
        role=role,
        group_id="group-1",
    )


@pytest.mark.asyncio
async def test_create_user_uses_callers_group_and_writes_both_systems():
    """Test the user is created in the identity provider and the table."""
    users_db = MockDatabase()
    provider = MockIdentityProvider()

    users = await create_user(
        users_db=users_db,
        identity_provider=provider,
        caller=_caller(),
        email="staff@example.com",
        user_name="Staff",
        role=UserRole.STAFF,
    )

    created_id = provider.accounts["staff@example.com"]
    assert [u.user_id for u in users] == [created_id]
    assert users[0].group_id == "group-1"
    assert users[0].role == UserRole.STAFF
    assert users[0].email == "staff@example.com"


@pytest.mark.asyncio
async def test_create_user_returns_only_the_callers_group():
    """Test users of other groups are not returned."""
    users_db = MockDatabase(
        [
            {
                "userId": "other",
                "userName": "Other",
                "role": "staff",
                "groupId": "group-2",
            },
        ],
    )

    users = await create_user(
        users_db=users_db,
        identity_provider=MockIdentityProvider(),
        caller=_caller(),
        email="staff@example.com",
        user_name="Staff",
        role=UserRole.STAFF,
    )

    assert {u.group_id for u in users} == {"group-1"}


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.STAFF, UserRole.ADMIN])
async def test_create_user_forbids_non_owner_callers(role):
    """Test only owners may create users."""
    provider = MockIdentityProvider()

    with pytest.raises(ClientAuthorizationError):
        await create_user(
            users_db=MockDatabase(),
            identity_provider=provider,
            caller=_caller(role),
            email="staff@example.com",
            user_name="Staff",
            role=UserRole.STAFF,
        )

    assert provider.accounts == {}


@pytest.mark.asyncio
async def test_create_user_rejects_admin_role():
    """Test an admin account cannot be created through this path."""
    provider = MockIdentityProvider()

    with pytest.raises(ClientValueError):
        await create_user(
            users_db=MockDatabase(),
            identity_provider=provider,
            caller=_caller(),
            email="admin@example.com",
            user_name="Admin",
            role=UserRole.ADMIN,
        )

    assert provider.accounts == {}


@pytest.mark.asyncio
async def test_create_user_rejects_existing_email():
    """Test a registered email address is rejected without writing a record."""
    users_db = MockDatabase()
    provider = MockIdentityProvider()
    await provider.create_user(email="staff@example.com", user_name="Staff")

    with pytest.raises(ClientValueError):
        await create_user(
            users_db=users_db,
            identity_provider=provider,
            caller=_caller(),
            email="staff@example.com",
            user_name="Staff",
            role=UserRole.STAFF,
        )

    assert users_db.items == []


@pytest.mark.asyncio
async def test_create_user_deletes_account_when_record_write_fails():
    """Test no half-created user remains when the table write fails."""
    users_db = MockDatabase()
    provider = MockIdentityProvider()

    with (
        patch.object(
            users_db,
            "put_item",
            new=AsyncMock(side_effect=RuntimeError("write failed")),
        ),
        pytest.raises(RuntimeError, match="write failed"),
    ):
        await create_user(
            users_db=users_db,
            identity_provider=provider,
            caller=_caller(),
            email="staff@example.com",
            user_name="Staff",
            role=UserRole.STAFF,
        )

    assert provider.accounts == {}
