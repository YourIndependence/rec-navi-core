# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /updateProject endpoint."""

from typing import cast
from uuid import uuid4

import pytest

from recnavi.apis.auth.auth import verify_user
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.main import app


def test_update_project_returns_401_when_no_token(client):
    """Test POST /updateProject returns 401 when no authorization header."""
    response = client.post(
        "/updateProject",
        json={
            "project": {
                "projectId": "proj-123",
                "projectName": "Updated Name",
                "description": "Updated Description",
                "assignedUserIds": [],
                "scenes": [],
                "version": 0,
            },
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
async def test_update_project_returns_good(
    client,
    auth_headers,
):
    """Test POST /updateProject successfully updates a project."""
    database = cast(
        dict[str, BaseDatabase],
        app.state.database,
    )[PROJECTS_TABLE_NAME]
    project_id = None
    try:
        create_response = client.post(
            "/createProject",
            headers=auth_headers,
            json={
                "projectName": "Original Project",
                "description": "Original Description",
                "scenePrincipals": ["cooking"],
                "assignedUserIds": [],
            },
        )
        assert create_response.status_code == 200
        created_project = create_response.json()["project"]
        project_id = created_project["projectId"]

        response = client.post(
            "/updateProject",
            headers=auth_headers,
            json={
                "project": {
                    "projectId": project_id,
                    "projectName": "Updated Project",
                    "description": "Updated Description",
                    "assignedUserIds": ["test-staff-456"],
                    "scenes": [
                        {
                            "sceneId": created_project["scenes"][0]["sceneId"],
                            "scenePrincipal": "cooking",
                            "assignedUserIds": ["test-staff-456"],
                        },
                    ],
                    "version": 0,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

        updated_project = data["project"]
        assert updated_project["projectId"] == project_id
        assert updated_project["projectName"] == "Updated Project"
        assert updated_project["description"] == "Updated Description"
        assert updated_project["assignedUserIds"] == ["test-staff-456"]
        assert updated_project["status"] == ProjectStatus.IN_PROGRESS
        assert updated_project["version"] == 1

        assert len(updated_project["scenes"]) == 1
        scene = updated_project["scenes"][0]
        assert scene["scenePrincipal"] == "cooking"
        assert scene["assignedUserIds"] == ["test-staff-456"]
        assert scene["videoUrl"] is None
        assert scene["thumbnailUrl"] is None
        assert "videoKey" not in scene
        assert "thumbnailKey" not in scene

        project_record = await database.get_item({"projectId": project_id})
        assert project_record is not None
        assert project_record["projectName"] == "Updated Project"
        assert project_record["description"] == "Updated Description"
        assert project_record["assignedUserIds"] == ["test-staff-456"]
        assert project_record["version"] == 1

    finally:
        if project_id:
            await database.delete_item(key={"projectId": project_id})


@pytest.mark.asyncio
async def test_update_project_returns_scene_urls_instead_of_keys(
    client,
    auth_headers,
):
    """Test POST /updateProject returns presigned urls and no keys."""
    databases = cast(dict[str, BaseDatabase], app.state.database)
    database = databases[PROJECTS_TABLE_NAME]
    project_id = f"test-update-project-{uuid4()}"
    previous_override = app.dependency_overrides[verify_user]
    try:
        await database.put_item(
            {
                "projectId": project_id,
                "groupId": "it-group",
                "ownerUserId": "owner-1",
                "projectName": "Project",
                "description": "",
                "assignedUserIds": [],
                "status": ProjectStatus.IN_PROGRESS,
                "version": 0,
                "createdAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-1",
                        "scenePrincipal": "cooking",
                        "status": "pending",
                        "videoKey": "videos/scene-1.mp4",
                        "thumbnailKey": "thumbnails/scene-1.jpg",
                    },
                ],
            },
        )
        app.dependency_overrides[verify_user] = lambda: User(
            user_id="owner-1",
            user_name="Owner",
            role=UserRole.OWNER,
            group_id="it-group",
        )
        response = client.post(
            "/updateProject",
            headers=auth_headers,
            json={
                "project": {
                    "projectId": project_id,
                    "projectName": "Renamed",
                    "description": "",
                    "assignedUserIds": [],
                    "scenes": [
                        {
                            "sceneId": "scene-1",
                            "scenePrincipal": "cooking",
                            "assignedUserIds": [],
                            "status": "pending",
                            "videoKey": "videos/scene-1.mp4",
                            "thumbnailKey": "thumbnails/scene-1.jpg",
                        },
                    ],
                    "version": 0,
                },
            },
        )
        assert response.status_code == 200
        scene = response.json()["project"]["scenes"][0]
        assert scene["videoUrl"].startswith(("mock://", "https://"))
        assert "videos/scene-1.mp4" in scene["videoUrl"]
        assert scene["thumbnailUrl"].startswith(("mock://", "https://"))
        assert "videoKey" not in scene
        assert "thumbnailKey" not in scene
    finally:
        app.dependency_overrides[verify_user] = previous_override
        await database.delete_item(key={"projectId": project_id})
