# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /updateProject endpoint."""

from contextlib import suppress
from typing import cast

import pytest

from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import ProjectStatus
from recnavi.main import app


def test_update_project_returns_400_when_no_token(client):
    """Test POST /updateProject returns 400 when no authorization header."""
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
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.real_aws
async def test_update_project_returns_good(
    client,
    auth_headers,
):
    """Test POST /updateProject successfully updates a project."""
    database = cast(
        dict[str, BaseDatabase],
        app.state.database,
    )[PROJECTS_TABLE_NAME]
    users_database = cast(
        dict[str, BaseDatabase],
        app.state.database,
    )[USERS_TABLE_NAME]
    await users_database.put_item(
        {
            "userId": "test-staff-456",
            "userName": "Test Staff",
            "role": "staff",
            "groupId": "it-group",
        },
    )
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

        update_response = client.post(
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
        assert update_response.status_code == 200
        data = update_response.json()
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

        project_record = await database.get_item({"projectId": project_id})
        assert project_record is not None
        assert project_record["projectName"] == "Updated Project"
        assert project_record["description"] == "Updated Description"
        assert project_record["assignedUserIds"] == ["test-staff-456"]
        assert project_record["version"] == 1

    finally:
        with suppress(Exception):
            if project_id:
                await database.delete_item(
                    {"projectId": project_id},
                )
        with suppress(Exception):
            await users_database.delete_item({"userId": "test-staff-456"})
