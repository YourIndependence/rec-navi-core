# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for Public (staff-facing) endpoints."""


def test_get_my_projects_returns_400_when_no_token(client):
    """Test GET /getMyProjects returns 400 when no authorization header."""
    response = client.get("/getMyProjects")
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


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


def test_submit_project_returns_400_when_no_token(client):
    """Test POST /submitProject returns 400 when no authorization header."""
    response = client.post(
        "/submitProject",
        json={"projectId": "proj-123"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
