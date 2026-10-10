# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for Public (staff-facing) endpoints."""


def test_get_my_projects_returns_401_when_no_token(client):
    """Test GET /getMyProjects returns 401 when no authorization header."""
    response = client.get("/getProjects")
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"
