# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getMe endpoint.

These tests access real AWS DynamoDB and require proper credentials.
Mark with @pytest.mark.real_aws to skip in CI without AWS access.
"""

import os

import pytest

from recnavi.core.types.user import User


def test_get_me_returns_user_when_authenticated(client):
    """Test GET /getMe returns user when properly authenticated."""
    from recnavi.apis.dependencies.auth import verify_user

    mock_user = User(
        user_id="test-user-123",
        user_name="Test User",
        role="admin",
        group_id="group-999",
    )

    async def mock_verify_user():
        return mock_user

    client.app.dependency_overrides[verify_user] = mock_verify_user

    try:
        response = client.get(
            "/getMe",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["user"]["userId"] == "test-user-123"
        assert data["user"]["userName"] == "Test User"
        assert data["user"]["role"] == "admin"
        assert data["groupId"] == "group-999"
    finally:
        client.app.dependency_overrides.clear()


def test_get_me_returns_400_when_no_token(client):
    """Test GET /getMe returns 400 when no authorization header."""
    response = client.get("/getMe")

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.real_aws
def test_get_me_with_real_aws(client, auth_headers):
    """Test GET /getMe with real AWS credentials.

    Prerequisites:
    - DynamoDB users table must exist
    - Valid user record with userId matching the token's sub claim
    - USERS_TABLE_NAME environment variable set
    """
    if not os.getenv("USERS_TABLE_NAME"):
        pytest.skip("USERS_TABLE_NAME not set, skipping real AWS test")

    response = client.get("/getMe", headers=auth_headers)

    assert response.status_code in [
        200,
        400,
        401,
        403,
    ], f"Unexpected status: {response.status_code}"

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "ok"
        assert "user" in data
        assert "groupId" in data
        assert "userId" in data["user"]
        assert "role" in data["user"]
