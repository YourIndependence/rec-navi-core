# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /updateSceneRecord endpoint."""


def test_update_scene_record_returns_400_when_no_token(client):
    """Test POST /updateSceneRecord returns 400 when no authorization header."""
    response = client.post(
        "/updateSceneRecord",
        json={
            "projectId": "proj-123",
            "sceneId": "scene-456",
            "video": "ZmFrZSB2aWRlbyBkYXRh",
            "thumbnail": "ZmFrZSB0aHVtYm5haWw=",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
