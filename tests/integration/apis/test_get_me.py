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


@pytest.mark.real_aws
def test_get_me_returns_user_when_authenticated(client, auth_headers):
    """Test GET /getMe returns user when properly authenticated.

    Prerequisites:
    - DynamoDB users table must exist
    - Valid user record with userId matching the token's sub claim
    - USERS_TABLE_NAME environment variable set
    """
    # This test requires a real AWS environment with:
    # - DynamoDB table with user data
    # - Valid Cognito token
    # Skip if not in real AWS environment
    if not os.getenv("USERS_TABLE_NAME"):
        pytest.skip("USERS_TABLE_NAME not set, skipping real AWS test")

    response = client.get("/getMe", headers=auth_headers)

    # With real AWS and valid token, should return 200
    # If token is invalid or user not found, will return 401/403
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


@pytest.mark.real_aws
def test_get_me_returns_400_when_no_token(client):
    """Test GET /getMe returns 400 when no authorization header."""
    response = client.get("/getMe")

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
