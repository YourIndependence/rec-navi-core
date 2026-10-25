# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /createUser endpoint."""

from uuid import uuid4

import pytest

from recnavi.apis.auth.auth import verify_user
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


def test_create_user_returns_400_when_no_token(client):
    """Test POST /createUser returns 400 when no authorization header."""
    response = client.post(
        "/createUser",
        json={
            "email": "staff@example.com",
            "userName": "Staff",
            "role": "staff",
        },
    )
    assert response.status_code == 400
    assert response.json()["status"] == "error"


def test_create_user_returns_403_when_caller_is_not_owner(
    client,
    auth_headers,
):
    """Test POST /createUser returns 403 for a non-owner caller."""
    response = client.post(
        "/createUser",
        headers=auth_headers,
        json={
            "email": "staff@example.com",
            "userName": "Staff",
            "role": "staff",
        },
    )
    assert response.status_code == 403
    assert response.json()["status"] == "error"


@pytest.mark.asyncio
async def test_create_user_success_preserves_group_and_db_identity(
    client,
    auth_headers,
):
    app = client.app
    previous = app.dependency_overrides[verify_user]
    group = f"it_group_{uuid4().hex}"
    email = f"it_{uuid4().hex}@example.com"
    caller = User(
        user_id="it_owner",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id=group,
    )
    app.dependency_overrides[verify_user] = lambda: caller
    created_id = None
    try:
        response = client.post(
            "/createUser",
            headers=auth_headers,
            json={
                "email": email,
                "userName": "Invited",
                "role": "staff",
                "groupId": "other",
            },
        )
        assert response.status_code == 200, response.text
        users = response.json()["users"]
        assert len(users) == 1
        assert users[0]["groupId"] == group
        assert users[0]["role"] == "staff"
        created_id = users[0]["userId"]
        item = await app.state.database[USERS_TABLE_NAME].get_item(
            {"userId": created_id},
        )
        assert item["email"] == email
        assert app.state.identity_provider.accounts[email] == created_id
    finally:
        app.dependency_overrides[verify_user] = previous
        if created_id is not None:
            await app.state.database[USERS_TABLE_NAME].delete_item(
                {"userId": created_id},
            )
        await app.state.identity_provider.delete_user(email=email)
