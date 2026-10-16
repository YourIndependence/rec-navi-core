# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /updateSceneRecord endpoint."""

from recnavi.apis.schemas.scene_schemas import UpdateSceneRecordResponse
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import SceneView
from recnavi.main import app


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


def test_openapi_schema_builds():
    """Test the OpenAPI schema generates (response models fully defined)."""
    assert app.openapi()["paths"]["/updateSceneRecord"]


def test_update_scene_record_response_accepts_a_project():
    """Test the response model can hold a Project and serialises it."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        status=ProjectStatus.IN_PROGRESS,
        owner_user_id="owner-1",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        scenes=[
            SceneView(
                scene_id="scene-456",
                scene_principal="cooking",
                video_key="private/video.mp4",
                thumbnail_key="private/thumbnail.jpg",
                video_url="https://example.test/video",
                thumbnail_url="https://example.test/thumbnail",
            ),
        ],
    )

    data = UpdateSceneRecordResponse(project=project).model_dump(
        by_alias=True,
        mode="json",
    )

    assert data["status"] == "ok"
    assert data["project"]["projectId"] == "proj-123"
    scene = data["project"]["scenes"][0]
    assert scene["videoUrl"] == "https://example.test/video"
    assert scene["thumbnailUrl"] == "https://example.test/thumbnail"
    assert "videoKey" not in scene
    assert "thumbnailKey" not in scene
