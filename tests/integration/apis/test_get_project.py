# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /getProject endpoint."""

from collections.abc import AsyncIterator
from contextlib import suppress
from typing import cast
from uuid import uuid4

import pytest
import pytest_asyncio

from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.main import app


@pytest_asyncio.fixture
async def project_data() -> AsyncIterator[dict[str, object]]:
    """Insert and remove a project used by this module."""
    database = cast(
        dict[str, BaseDatabase],
        app.state.database,
    )[PROJECTS_TABLE_NAME]
    item = {
        "projectId": f"it_{uuid4()}",
        "groupId": "it-group",
        "projectName": "Integration Test Project",
        "description": "Test project for integration testing",
        "ownerUserId": "test-user-123",
        "assignedUserIds": ["dummy_user_id"],
        "createdAt": "2026-09-21T00:00:00Z",
        "updatedAt": "2026-09-21T00:00:00Z",
        "status": "in_progress",
        "version": 0,
        "scenes": [],
    }
    await database.put_item(item)

    try:
        yield item
    finally:
        with suppress(Exception):
            await database.delete_item(
                {"projectId": item["projectId"]},
            )


def test_get_project_returns_400_when_no_token(client):
    """Test POST /getProject returns 400 when no authorization header."""
    response = client.post(
        "/getProject",
        json={"projectId": "proj-123"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_get_project_returns_400_when_missing_project_id(client, auth_headers):
    """Test POST /getProject returns 400 when projectId is missing."""
    response = client.post(
        "/getProject",
        headers=auth_headers,
        json={},  # Missing projectId
    )

    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_projects_returns_injected_project(
    client,
    auth_headers,
    project_data: dict[str, object],
):
    """Return the project injected for this integration test."""
    response = client.get("/getProjects", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert project_data in data["projects"]
