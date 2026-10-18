# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /reviewScene endpoint."""

import pytest

from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.main import app


def test_review_scene_returns_400_when_no_token(client):
    """Test POST /reviewScene returns 400 when no authorization header."""
    response = client.post(
        "/reviewScene",
        json={
            "projectId": "proj-123",
            "sceneId": "scene-456",
            "result": "approved",
            "comment": "Looks good!",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_openapi_schema_builds(client):
    """The HTTP OpenAPI endpoint includes the review route."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["paths"]["/reviewScene"]


@pytest.mark.asyncio
async def test_review_scene_persists_review_through_http(client, auth_headers):
    """Review writes metadata and version and returns a client-safe project."""
    create_response = client.post(
        "/createProject",
        headers=auth_headers,
        json={
            "projectName": "Review Project",
            "description": "",
            "scenePrincipals": ["cooking"],
            "assignedUserIds": [],
        },
    )
    assert create_response.status_code == 200
    project = create_response.json()["project"]
    project_id = project["projectId"]
    database = app.state.database[PROJECTS_TABLE_NAME]
    try:
        response = client.post(
            "/reviewScene",
            headers=auth_headers,
            json={
                "projectId": project_id,
                "sceneId": project["scenes"][0]["sceneId"],
                "result": "rejected",
                "comment": "Please re-record",
            },
        )
        assert response.status_code == 200
        data = response.json()["project"]
        assert data["version"] == 1
        scene = data["scenes"][0]
        assert scene["status"] == "rejected"
        assert scene["reviewComment"] == "Please re-record"
        assert scene["reviewedBy"] == "test-user-123"
        assert scene["reviewedAt"] is not None
        assert "videoKey" not in scene
        assert "thumbnailKey" not in scene
        saved = await database.get_item({"projectId": project_id})
        assert saved["version"] == data["version"]
        assert saved["scenes"][0]["reviewComment"] == scene["reviewComment"]
    finally:
        await database.delete_item({"projectId": project_id})
