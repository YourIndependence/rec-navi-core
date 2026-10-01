# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /downloadProject endpoint."""


def test_download_project_returns_400_when_no_token(client):
    """Test POST /downloadProject returns 400 when no authorization header."""
    response = client.post(
        "/downloadProject",
        json={"projectId": "proj-123"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
