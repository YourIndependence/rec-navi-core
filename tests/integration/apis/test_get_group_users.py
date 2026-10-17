# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getGroupUsers endpoint."""

from recnavi.apis.auth.auth import verify_user
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.main import app
from tests.mockups.mock_database import MockDatabase


def test_get_group_users_returns_400_when_no_token(client):
    """Test GET /getGroupUsers returns 400 when no authorization header."""
    response = client.get("/getGroupUsers")
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_get_group_users_returns_only_current_groups_public_members(
    client,
    auth_headers,
    monkeypatch,
):
    caller = User(
        user_id="owner",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group-1",
    )
    monkeypatch.setitem(app.dependency_overrides, verify_user, lambda: caller)
    monkeypatch.setitem(
        app.state.database,
        USERS_TABLE_NAME,
        MockDatabase(
            initial_items=[
                {
                    "userId": "member",
                    "userName": "Member",
                    "role": "staff",
                    "groupId": "group-1",
                    "email": "private@example.com",
                    "phoneNumber": "123",
                    "birthday": "2000-01-01",
                    "profileImageUri": "s3://private/avatar",
                },
                {
                    "userId": "outsider",
                    "userName": "Other",
                    "role": "staff",
                    "groupId": "group-2",
                },
            ],
        ),
    )
    response = client.get(
        "/getGroupUsers?groupId=group-2",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "users": [
            {"userId": "member", "userName": "Member", "role": "staff"},
        ],
    }


def test_get_group_users_rejects_staff(client, auth_headers, monkeypatch):
    caller = User(
        user_id="staff",
        user_name="Staff",
        role=UserRole.STAFF,
        group_id="group-1",
    )
    monkeypatch.setitem(app.dependency_overrides, verify_user, lambda: caller)
    response = client.get("/getGroupUsers", headers=auth_headers)
    assert response.status_code == 403
    assert response.json()["status"] == "error"


def test_get_group_users_returns_empty_list(client, auth_headers, monkeypatch):
    monkeypatch.setitem(app.state.database, USERS_TABLE_NAME, MockDatabase())
    response = client.get("/getGroupUsers", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["users"] == []
