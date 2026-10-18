# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""HTTP submission contract through real use-case and database boundaries."""

from typing import cast
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from recnavi.apis.auth.auth import verify_user
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


def test_submit_project_returns_400_when_no_token(client):
    """Reject missing authentication headers."""
    response = client.post("/submitProject", json={"projectId": "proj-123"})
    assert response.status_code == 400
    assert response.json()["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scene_status,missing",
    [
        (SceneStatus.PENDING, []),
        (SceneStatus.APPROVED, []),
        (SceneStatus.NOT_RECORDED, ["scene-1"]),
        (SceneStatus.REJECTED, ["scene-1"]),
    ],
)
async def test_submit_project_persists_and_retries_through_http(
    client: TestClient,
    auth_headers: dict[str, str],
    scene_status: SceneStatus,
    missing: list[str],
) -> None:
    """Exercise successful submission, retry, and incomplete shooting via HTTP."""
    database = cast(
        BaseDatabase,
        client.app.state.database[PROJECTS_TABLE_NAME],
    )
    project = Project(
        project_id=f"it_submit_{uuid4().hex}",
        project_name="Submission",
        group_id="it-group",
        owner_user_id="owner-1",
        assigned_user_ids=["staff-1"],
        created_at="2026-01-01T00:00:00Z",
        version=3,
        scenes=[
            Scene(
                scene_id="scene-1",
                scene_principal="intro",
                status=scene_status,
                video_key="videos/test.mp4",
                thumbnail_key="thumbs/test.jpg",
            ),
        ],
    )
    original_override = client.app.dependency_overrides[verify_user]
    client.app.dependency_overrides[verify_user] = lambda: User(
        user_id="staff-1",
        user_name="Staff",
        role=UserRole.STAFF,
        group_id="it-group",
    )
    try:
        await database.put_item(project.model_dump(by_alias=True))
        for _ in range(2):
            response = client.post(
                "/submitProject",
                headers=auth_headers,
                json={"projectId": project.project_id},
            )
            assert response.status_code == 200, response.text
            data = response.json()
            assert data["missingSceneIds"] == missing
            assert data["project"]["status"] == (
                "in_progress" if missing else "submitted"
            )
            assert data["project"]["version"] == (3 if missing else 4)
            scene = data["project"]["scenes"][0]
            assert scene["videoUrl"]
            assert scene["thumbnailUrl"]
            assert "videoKey" not in scene
            assert "thumbnailKey" not in scene
        stored = await database.get_item({"projectId": project.project_id})
        assert stored is not None
        assert stored["status"] == response.json()["project"]["status"]
        assert stored["version"] == (3 if missing else 4)
        assert stored["scenes"][0]["videoKey"] == "videos/test.mp4"
    finally:
        client.app.dependency_overrides[verify_user] = original_override
        await database.delete_item({"projectId": project.project_id})
