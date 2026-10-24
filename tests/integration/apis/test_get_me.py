# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getMe with the shared auth override."""


def test_get_me_returns_401_when_no_token(client):
    """Test GET /getMe returns 401 when no authorization header."""
    response = client.get("/getMe")

    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


def test_get_me_returns_authenticated_user(client, auth_headers):
    """Return the user provided by the shared authentication override."""
    response = client.get("/getMe", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    user = data["user"]
    assert user["userId"] == "test-user-123"
    assert user["userName"] == "Test User"
    assert user["groupId"] == "it-group"
    assert user["role"] == "admin"
