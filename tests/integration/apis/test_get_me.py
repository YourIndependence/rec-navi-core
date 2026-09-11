# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getMe endpoint."""

import pytest
from moto import mock_aws
from unittest.mock import AsyncMock, patch

from recnavi.config.variables import USERS_TABLE_NAME


@pytest.fixture
def mock_decode_token():
    """Mock decode_token to return a valid payload."""

    async def _decode_token(request):
        return {"sub": "test-user-123", "email": "test@example.com"}

    return _decode_token


@pytest.fixture
def mock_user_database():
    """Mock UserDatabase with test data."""

    class MockUserDatabase:
        def __init__(self):
            self.users = {
                "test-user-123": {
                    "userId": "test-user-123",
                    "userName": "Test User",
                    "role": "admin",
                    "groupId": "group-456",
                },
                "owner-user": {
                    "userId": "owner-user",
                    "userName": "Owner User",
                    "role": "owner",
                    "groupId": "group-789",
                },
                "staff-user": {
                    "userId": "staff-user",
                    "userName": "Staff User",
                    "role": "staff",
                    "groupId": "group-101",
                },
            }

        async def get_item(self, key: dict):
            user_id = key.get("userId")
            return self.users.get(user_id)

        async def put_item(self, item: dict):
            pass

        async def query(self, key_condition: dict, _filter_expression=None):
            return []

        async def delete_item(self, key: dict):
            pass

    return MockUserDatabase()


def test_get_me_returns_user_when_authenticated(
    client, mock_decode_token, mock_user_database
):
    """Test GET /getMe returns user data for authenticated user."""
    with patch("recnavi.apis.root.root_router.decode_token", mock_decode_token):
        client.app.state.database = {USERS_TABLE_NAME: mock_user_database}

        response = client.get(
            "/getMe",
            headers={
                "Authorization": "Bearer valid_token",
                "Client-Id": "test_client",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["message"] is None
        assert data["user"]["userId"] == "test-user-123"
        assert data["user"]["userName"] == "Test User"
        assert data["user"]["role"] == "admin"
        assert data["user"]["groupId"] == "group-456"
        assert data["groupId"] == "group-456"


def test_get_me_returns_owner_role(client, mock_user_database):
    """Test GET /getMe returns owner role correctly."""

    async def _decode_token_owner(request):
        return {"sub": "owner-user", "email": "owner@example.com"}

    with patch("recnavi.apis.root.root_router.decode_token", _decode_token_owner):
        client.app.state.database = {USERS_TABLE_NAME: mock_user_database}

        response = client.get(
            "/getMe",
            headers={
                "Authorization": "Bearer valid_token",
                "Client-Id": "test_client",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "owner"
        assert data["user"]["groupId"] == "group-789"
        assert data["groupId"] == "group-789"


def test_get_me_returns_staff_role(client, mock_user_database):
    """Test GET /getMe returns staff role correctly."""

    async def _decode_token_staff(request):
        return {"sub": "staff-user", "email": "staff@example.com"}

    with patch("recnavi.apis.root.root_router.decode_token", _decode_token_staff):
        client.app.state.database = {USERS_TABLE_NAME: mock_user_database}

        response = client.get(
            "/getMe",
            headers={
                "Authorization": "Bearer valid_token",
                "Client-Id": "test_client",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "staff"


def test_get_me_returns_400_when_no_token(client, mock_user_database):
    """Test GET /getMe returns 400 when Authorization header missing."""
    client.app.state.database = {USERS_TABLE_NAME: mock_user_database}

    response = client.get("/getMe")

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_get_me_returns_403_when_user_not_in_database(client):
    """Test GET /getMe returns 403 when user not found in database."""

    async def _decode_token_unknown(request):
        return {"sub": "unknown-user", "email": "unknown@example.com"}

    class EmptyUserDatabase:
        async def get_item(self, key: dict):
            return None

        async def put_item(self, item: dict):
            pass

        async def query(self, key_condition: dict, _filter_expression=None):
            return []

        async def delete_item(self, key: dict):
            pass

    with patch("recnavi.apis.root.root_router.decode_token", _decode_token_unknown):
        client.app.state.database = {USERS_TABLE_NAME: EmptyUserDatabase()}

        response = client.get(
            "/getMe",
            headers={
                "Authorization": "Bearer valid_token",
                "Client-Id": "test_client",
            },
        )

        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "error"
        assert "User not found" in data["message"]


def test_get_me_returns_403_for_invalid_role(client):
    """Test GET /getMe returns 403 when user has invalid role."""

    async def _decode_token_invalid_role(request):
        return {"sub": "invalid-role-user", "email": "invalid@example.com"}

    class InvalidRoleDatabase:
        async def get_item(self, key: dict):
            return {
                "userId": "invalid-role-user",
                "userName": "Invalid Role User",
                "role": "superadmin",
                "groupId": "group-999",
            }

        async def put_item(self, item: dict):
            pass

        async def query(self, key_condition: dict, _filter_expression=None):
            return []

        async def delete_item(self, key: dict):
            pass

    with patch(
        "recnavi.apis.root.root_router.decode_token", _decode_token_invalid_role
    ):
        client.app.state.database = {USERS_TABLE_NAME: InvalidRoleDatabase()}

        response = client.get(
            "/getMe",
            headers={
                "Authorization": "Bearer valid_token",
                "Client-Id": "test_client",
            },
        )

        assert response.status_code == 403
        data = response.json()
        assert data["status"] == "error"
        assert "Invalid role" in data["message"]


def test_get_me_group_id_not_duplicated_in_user(
    client, mock_decode_token, mock_user_database
):
    """Test GET /getMe has groupId at top level, not duplicated in user."""
    with patch("recnavi.apis.root.root_router.decode_token", mock_decode_token):
        client.app.state.database = {USERS_TABLE_NAME: mock_user_database}

        response = client.get(
            "/getMe",
            headers={
                "Authorization": "Bearer valid_token",
                "Client-Id": "test_client",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "groupId" in data
        assert data["groupId"] == "group-456"
        assert data["user"]["groupId"] == "group-456"


def test_get_me_field_names_are_camel_case(
    client, mock_decode_token, mock_user_database
):
    """Test GET /getMe response uses camelCase field names."""
    with patch("recnavi.apis.root.root_router.decode_token", mock_decode_token):
        client.app.state.database = {USERS_TABLE_NAME: mock_user_database}

        response = client.get(
            "/getMe",
            headers={
                "Authorization": "Bearer valid_token",
                "Client-Id": "test_client",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "userId" in data["user"]
        assert "userName" in data["user"]
        assert "groupId" in data["user"]
        assert "groupId" in data

        assert "user_id" not in data["user"]
        assert "user_name" not in data["user"]
        assert "group_id" not in data
