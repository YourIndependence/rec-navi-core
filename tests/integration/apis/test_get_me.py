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

import pytest


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
    response = client.get("/getMe", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["groupId"] == "it-group"
    user = data["user"]
    assert user["userId"] == "test-user-123"
    assert user["userName"] == "Test User"
    assert user["groupId"] == "it-group"
    assert user["role"] == "owner"
