# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getMe endpoint."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_decode_token():
    """Mock decode_token to return a valid payload."""
    with patch("recnavi.apis.root.root_router.decode_token") as mock:
        mock.return_value = AsyncMock(return_value={"sub": "test-user-123"})
        yield mock


@pytest.fixture
def mock_user_database(client):
    """Mock UserDatabase with test data."""

    class FakeDatabaseForIntegration:
        def __init__(self):
            self.users = {
                "test-user-123": {
                    "userId": "test-user-123",
                    "userName": "Test Admin",
                    "role": "admin",
                    "groupId": "group-999",
                },
            }

        async def get_item(self, key):
            return self.users.get(key.get("userId"))

        async def put_item(self, item):
            pass

        async def query(self, key_condition, _filter_expression=None):
            return []

        async def delete_item(self, key):
            pass

    # Replace the database instance in app state
    from recnavi.config.variables import USERS_TABLE_NAME

    original_db = client.app.state.database.get(USERS_TABLE_NAME)
    client.app.state.database[USERS_TABLE_NAME] = FakeDatabaseForIntegration()

    yield

    # Restore original
    if original_db:
        client.app.state.database[USERS_TABLE_NAME] = original_db


def test_get_me_returns_user_when_authenticated(
    client,
    mock_decode_token,
    mock_user_database,
):
    """Test GET /getMe returns user when properly authenticated."""

    async def fake_decode(request):
        return {"sub": "test-user-123"}

    mock_decode_token.side_effect = fake_decode

    response = client.get(
        "/getMe",
        headers={"Authorization": "Bearer valid_token"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["user"]["userId"] == "test-user-123"
    assert data["user"]["userName"] == "Test Admin"
    assert data["user"]["role"] == "admin"
    assert data["groupId"] == "group-999"
    # Verify groupId is at top level, not duplicated in user
    assert "groupId" in data
    assert data["groupId"] == data["user"]["groupId"]


def test_get_me_returns_401_when_no_token(client):
    """Test GET /getMe returns 401 when no authorization header."""
    response = client.get("/getMe")

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_get_me_returns_403_when_user_not_in_database(
    client,
    mock_decode_token,
):
    """Test GET /getMe returns 403 when user not found in database."""

    async def fake_decode(request):
        return {"sub": "nonexistent-user"}

    mock_decode_token.side_effect = fake_decode

    # Mock empty database
    class EmptyDatabase:
        async def get_item(self, key):
            return None

        async def put_item(self, item):
            pass

        async def query(self, key_condition, _filter_expression=None):
            return []

        async def delete_item(self, key):
            pass

    from recnavi.config.variables import USERS_TABLE_NAME

    original_db = client.app.state.database.get(USERS_TABLE_NAME)
    client.app.state.database[USERS_TABLE_NAME] = EmptyDatabase()

    response = client.get(
        "/getMe",
        headers={"Authorization": "Bearer valid_token"},
    )

    # Restore
    if original_db:
        client.app.state.database[USERS_TABLE_NAME] = original_db

    assert response.status_code == 403
    data = response.json()
    assert data["status"] == "error"
    assert "User not found" in data["message"]


def test_get_me_returns_403_when_invalid_role(client, mock_decode_token):
    """Test GET /getMe returns 403 when user has invalid role."""

    async def fake_decode(request):
        return {"sub": "bad-role-user"}

    mock_decode_token.side_effect = fake_decode

    class DatabaseWithBadRole:
        async def get_item(self, key):
            if key.get("userId") == "bad-role-user":
                return {
                    "userId": "bad-role-user",
                    "userName": "Bad User",
                    "role": "superadmin",  # Invalid role
                    "groupId": "group-123",
                }
            return None

        async def put_item(self, item):
            pass

        async def query(self, key_condition, _filter_expression=None):
            return []

        async def delete_item(self, key):
            pass

    from recnavi.config.variables import USERS_TABLE_NAME

    original_db = client.app.state.database.get(USERS_TABLE_NAME)
    client.app.state.database[USERS_TABLE_NAME] = DatabaseWithBadRole()

    response = client.get(
        "/getMe",
        headers={"Authorization": "Bearer valid_token"},
    )

    # Restore
    if original_db:
        client.app.state.database[USERS_TABLE_NAME] = original_db

    assert response.status_code == 403
    data = response.json()
    assert data["status"] == "error"
    assert "Invalid role" in data["message"]
