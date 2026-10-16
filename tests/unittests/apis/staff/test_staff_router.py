# Copyright (c) 2026 YourIndependence. All rights reserved.

"""HTTP parsing and use-case delegation for scene recordings."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneView
from tests.mockups.mock_users import get_mock_x_user


def _make_project() -> Project:
    return Project(
        project_id="proj-123",
        project_name="Test Project",
        description="Project description",
        status=ProjectStatus.IN_PROGRESS,
        scenes=[Scene(scene_id="scene-456", scene_principal="cooking")],
        owner_user_id="test-user-123",
        assigned_user_ids=["staff-456"],
        group_id="it-group",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
        version=3,
    )


def test_get_projects_parses_pagination_and_serializes_response(
    staff_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    project = _make_project()
    with patch(
        "recnavi.apis.staff.staff_router.get_projects_usecase",
        new=AsyncMock(return_value=([project], "next-page")),
    ) as usecase:
        response = staff_client.get(
            "/getProjects?limit=12&cursor=previous-page",
            headers=auth_headers,
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "projects": [project.model_dump(by_alias=True, mode="json")],
        "nextCursor": "next-page",
    }
    usecase.assert_awaited_once_with(
        projects_db=staff_client.app.state.database[PROJECTS_TABLE_NAME],
        user_id="test-user-123",
        group_id="it-group",
        limit=12,
        cursor="previous-page",
    )


def test_get_project_parses_request_and_serializes_response(
    staff_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    project = _make_project()
    with patch(
        "recnavi.apis.staff.staff_router.get_project_usecase",
        new=AsyncMock(return_value=project),
    ) as usecase:
        response = staff_client.post(
            "/getProject",
            headers=auth_headers,
            json={"projectId": "proj-123"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "project": project.model_dump(by_alias=True, mode="json"),
    }
    usecase.assert_awaited_once_with(
        projects_db=staff_client.app.state.database[PROJECTS_TABLE_NAME],
        project_id="proj-123",
        user=get_mock_x_user(),
    )


def test_update_scene_record_parses_request_and_serializes_usecase_result(
    staff_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Pass camelCase input to the use case and expose its public scene URLs."""
    project = Project(
        project_id="proj-123",
        project_name="Test Project",
        group_id="it-group",
        owner_user_id="test-user-123",
        created_at="2026-01-01T00:00:00Z",
        scenes=[
            SceneView(
                scene_id="scene-456",
                scene_principal="cooking",
                video_key="private/video.mp4",
                thumbnail_key="private/thumbnail.jpg",
                video_url="https://example.com/video",
                thumbnail_url="https://example.com/thumbnail",
            ),
        ],
    )
    with patch(
        "recnavi.apis.staff.staff_router.update_scene_record_usecase",
        new=AsyncMock(return_value=project),
    ) as usecase:
        response = staff_client.post(
            "/updateSceneRecord",
            headers=auth_headers,
            json={
                "projectId": "proj-123",
                "sceneId": "scene-456",
                "video": "dmlkZW8=",
                "thumbnail": "dGh1bWI=",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "project": project.model_dump(by_alias=True, mode="json"),
    }
    scene = response.json()["project"]["scenes"][0]
    assert scene["videoUrl"] == "https://example.com/video"
    assert scene["thumbnailUrl"] == "https://example.com/thumbnail"
    assert "videoKey" not in scene
    assert "thumbnailKey" not in scene
    usecase.assert_awaited_once_with(
        projects_db=staff_client.app.state.database[PROJECTS_TABLE_NAME],
        storage=staff_client.app.state.object_storage,
        project_id="proj-123",
        scene_id="scene-456",
        video_base64="dmlkZW8=",
        thumbnail_base64="dGh1bWI=",
        user=get_mock_x_user(),
    )


@pytest.mark.parametrize(
    "missing_field",
    ["projectId", "sceneId", "video", "thumbnail"],
)
def test_update_scene_record_rejects_missing_fields_without_calling_usecase(
    staff_client: TestClient,
    missing_field: str,
) -> None:
    """Reject incomplete request bodies before invoking application logic."""
    payload = {
        "projectId": "p1",
        "sceneId": "s1",
        "video": "eA==",
        "thumbnail": "eA==",
    }
    del payload[missing_field]
    with patch(
        "recnavi.apis.staff.staff_router.update_scene_record_usecase",
        new=AsyncMock(),
    ) as usecase:
        response = staff_client.post("/updateSceneRecord", json=payload)
    assert response.status_code == 422
    usecase.assert_not_awaited()
