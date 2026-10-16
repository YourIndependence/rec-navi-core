# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /deleteProject endpoint."""

from contextlib import suppress
from typing import cast

import pytest

from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.main import app


def test_delete_project_returns_400_when_no_token(client):
    """Test POST /deleteProject returns 400 when no authorization header."""
    response = client.post(
        "/deleteProject",
        json={"projectId": "proj-123"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
async def test_delete_project_returns_good(
    client,
    auth_headers,
):
    """Test POST /deleteProject successfully deletes a project."""
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
                "projectName": "Project to Delete",
                "description": "Will be deleted",
                "scenePrincipals": ["cooking"],
                "assignedUserIds": [],
            },
        )
        assert create_response.status_code == 200
        created_project = create_response.json()["project"]
        project_id = created_project["projectId"]

        response = client.post(
            "/deleteProject",
            headers=auth_headers,
            json={"projectId": project_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["projectId"] == project_id

        project_record = await database.get_item({"projectId": project_id})
        assert project_record is None

    finally:
        with suppress(Exception):
            if project_id:
                await database.delete_item(
                    {"projectId": project_id},
                )
