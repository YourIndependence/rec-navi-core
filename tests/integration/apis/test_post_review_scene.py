# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /reviewScene endpoint."""


def test_review_scene_returns_400_when_no_token(client):
    """Test POST /reviewScene returns 400 when no authorization header."""
    response = client.post(
        "/reviewScene",
        json={
            "projectId": "proj-123",
            "sceneId": "scene-456",
            "result": "approve",
            "comment": "Looks good!",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
