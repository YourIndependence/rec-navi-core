# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getSceneMasters endpoint."""

from contextlib import suppress
from typing import cast

import pytest

from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import ProjectStatus
from recnavi.main import app


def test_create_project_returns_400_when_no_token(client):
    """Test POST /createProject returns 400 when no authorization header."""
    response = client.post(
        "/createProject",
        json={
            "projectName": "Test Project",
            "description": "Test Description",
            "scenePrincipals": ["cooking"],
            "assignedUserIds": [],
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.real_aws
async def test_create_project_returns_good(
    client,
    auth_headers,
):
    """Test POST /createProject returns 400 when no authorization header."""
    database = cast(
        dict[str, BaseDatabase],
        app.state.database,
    )[PROJECTS_TABLE_NAME]
    project_id = None
    try:
        response = client.post(
            "/createProject",
            headers=auth_headers,
            json={
                "projectName": "Test Project",
                "description": "Test Description",
                "scenePrincipals": ["cooking"],
                "assignedUserIds": [],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

        project = data["project"]
        project_id = project["projectId"]
        assert isinstance(project_id, str)
        assert project["projectName"] == "Test Project"
        assert project["description"] == "Test Description"
        assert project["status"] == ProjectStatus.IN_PROGRESS

        assert isinstance(project["scenes"], list)
        assert len(project["scenes"]) == 1
        scene = project["scenes"][0]
        assert isinstance(scene["sceneId"], str)
        assert scene["scenePrincipal"] == "cooking"
        assert scene["status"] == "not_recorded"
        assert scene["videoKey"] is None
        assert scene["thumbnailKey"] is None
        assert scene["createdBy"] is None
        assert scene["createdAt"] is None
        assert scene["assignedAt"] is None
        assert scene["assignedUserIds"] == []

        assert project["ownerUserId"] == "test-user-123"
        assert project["assignedUserIds"] == []
        assert project["groupId"] == "it-group"
        assert isinstance(project["createdAt"], str)
        assert isinstance(project["updatedAt"], str)
        assert project["version"] == 0

        project_recode = await database.get_item({"projectId": project_id})
        assert project_recode is not None
        assert project_recode["projectName"] == "Test Project"
        assert project_recode["description"] == "Test Description"
        assert project_recode["status"] == ProjectStatus.IN_PROGRESS

        assert isinstance(project_recode["scenes"], list)
        assert len(project_recode["scenes"]) == 1
        scene_recode = project_recode["scenes"][0]
        assert isinstance(scene_recode["sceneId"], str)
        assert scene_recode["scenePrincipal"] == "cooking"
        assert scene_recode["status"] == "not_recorded"
        assert scene_recode["videoKey"] is None
        assert scene_recode["thumbnailKey"] is None
        assert scene_recode["createdBy"] is None
        assert scene_recode["createdAt"] is None
        assert scene_recode["assignedAt"] is None
        assert scene_recode["assignedUserIds"] == []

        assert project_recode["ownerUserId"] == "test-user-123"
        assert project_recode["assignedUserIds"] == []
        assert project_recode["groupId"] == "it-group"
        assert isinstance(project_recode["createdAt"], str)
        assert isinstance(project_recode["updatedAt"], str)
        assert project_recode["version"] == 0

    finally:
        with suppress(Exception):
            await database.delete_item(
                {"projectId": project_id},
            )
