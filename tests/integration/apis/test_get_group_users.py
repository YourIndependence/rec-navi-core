# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getGroupUsers endpoint."""

from collections.abc import AsyncIterator
from collections.abc import Iterator
from typing import cast
from uuid import uuid4

import pytest
import pytest_asyncio

from recnavi.apis.auth.auth import verify_user
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.main import app


@pytest.fixture
def group_caller() -> Iterator[User]:
    """Isolate the authenticated group and restore its authentication boundary."""
    caller = User(
        user_id=f"owner-{uuid4().hex}",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id=f"group-{uuid4().hex}",
    )
    previous_override = app.dependency_overrides[verify_user]
    app.dependency_overrides[verify_user] = lambda: caller
    try:
        yield caller
    finally:
        app.dependency_overrides[verify_user] = previous_override


@pytest_asyncio.fixture
async def group_members(
    group_caller: User,
) -> AsyncIterator[tuple[User, User]]:
    """Seed the existing database and clean up without replacing components."""
    database = cast(BaseDatabase, app.state.database[USERS_TABLE_NAME])
    member = User(
        user_id=f"member-{uuid4().hex}",
        user_name="Member",
        role=UserRole.STAFF,
        group_id=group_caller.group_id,
        email="private@example.com",
        phone_number="123",
        birthday="2000-01-01",
        profile_image_uri="s3://private/avatar",
    )
    outsider = User(
        user_id=f"outsider-{uuid4().hex}",
        user_name="Other",
        role=UserRole.STAFF,
        group_id=f"other-group-{uuid4().hex}",
    )
    try:
        for user in (member, outsider):
            await database.put_item(user.model_dump(by_alias=True))
        yield member, outsider
    finally:
        for user in (member, outsider):
            await database.delete_item(key={"userId": user.user_id})


def test_get_group_users_returns_400_when_no_token(client):
    """Reject requests without authentication."""
    response = client.get("/getGroupUsers")
    assert response.status_code == 400
    assert response.json()["status"] == "error"


def test_get_group_users_returns_only_current_groups_public_members(
    client,
    auth_headers,
    group_members,
):
    """Keep tenant isolation and expose only the agreed member fields."""
    member, _ = group_members
    response = client.get(
        "/getGroupUsers",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "users": [
            {
                "userId": member.user_id,
                "userName": "Member",
                "role": "staff",
                "groupId": member.group_id,
                "profileImageUri": "s3://private/avatar",
            },
        ],
    }


def test_get_group_users_rejects_staff(client, auth_headers, group_caller):
    """Exercise authorization through the real HTTP and application path."""
    group_caller.role = UserRole.STAFF
    response = client.get("/getGroupUsers", headers=auth_headers)
    assert response.status_code == 403
    assert response.json()["status"] == "error"


def test_get_group_users_returns_empty_list(
    client,
    auth_headers,
    group_caller,
):
    """A new group has no members in the existing database."""
    response = client.get("/getGroupUsers", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["users"] == []
