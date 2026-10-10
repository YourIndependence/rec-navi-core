# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /reviewScene endpoint."""

from recnavi.apis.schemas.scene_schemas import ReviewSceneResponse
from recnavi.core.types.project import Project
from recnavi.main import app


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


def test_openapi_schema_builds():
    """Test the OpenAPI schema generates (response models fully defined)."""
    assert app.openapi()["paths"]["/reviewScene"]


def test_review_scene_response_accepts_a_project():
    """Test the response model can hold a Project and serialises it."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="owner-1",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        scenes=[],
    )

    data = ReviewSceneResponse(project=project).model_dump(
        by_alias=True, mode="json"
    )

    assert data["status"] == "ok"
    assert data["project"]["projectId"] == "proj-123"
