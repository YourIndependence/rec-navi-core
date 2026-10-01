# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getGroupUsers endpoint."""


def test_get_group_users_returns_400_when_no_token(client):
    """Test GET /getGroupUsers returns 400 when no authorization header."""
    response = client.get("/getGroupUsers")
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
