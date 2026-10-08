# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /createUser endpoint."""


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
