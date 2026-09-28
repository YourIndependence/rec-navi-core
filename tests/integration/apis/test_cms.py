# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for CMS endpoints.

Some tests require real AWS DynamoDB access and are marked with
@pytest.mark.real_aws to skip in CI environments.

Other tests verify basic HTTP behavior without AWS dependencies.
"""

from collections.abc import AsyncIterator
from contextlib import suppress
from typing import cast
from uuid import uuid4

import pytest
import pytest_asyncio

from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.main import app


@pytest_asyncio.fixture
async def scene_master_data() -> AsyncIterator[dict[str, object]]:
    """Insert and remove a scene master used by this module."""
    database = cast(
        dict[str, BaseDatabase],
        app.state.database,
    )[SCENES_TABLE_NAME]
    item = {
        "scenePrincipal": f"it_{uuid4()}",
        "title": "Integration Test Scene",
        "thumbnailUri": "s3://it-test/thumbnail.jpg",
        "guideUri": "s3://it-test/guide.png",
        "maxDurationSeconds": 30,
    }
    await database.put_item(item)

    try:
        yield item
    finally:
        with suppress(Exception):
            await database.delete_item(
                {"scenePrincipal": item["scenePrincipal"]},
            )


@pytest_asyncio.fixture
async def template_data() -> AsyncIterator[dict[str, object]]:
    """Insert and remove a template used by this module."""
    database = cast(
        dict[str, BaseDatabase],
        app.state.database,
    )[TEMPLATES_TABLE_NAME]
    item = {
        "templateId": f"it_{uuid4()}",
        "title": "Integration Test Template",
        "scenePrincipals": ["it_scene_master"],
        "thumbnailUri": "s3://it-test/template.jpg",
    }
    await database.put_item(item)

    try:
        yield item
    finally:
        with suppress(Exception):
            await database.delete_item(
                {"templateId": item["templateId"]},
            )


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
        "ownerUserId": "dummy_user_id",
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


def test_get_scene_masters_returns_400_when_no_token(client):
    """Test GET /getSceneMasters returns 400 when no authorization header."""
    response = client.get("/getSceneMasters")

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.real_aws
async def test_get_scene_masters_returns_injected_scene(
    client,
    auth_headers,
    scene_master_data: dict[str, object],
):
    """Return the scene master injected for this integration test."""
    response = client.get("/getSceneMasters", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert {
        "scenePrincipal": scene_master_data["scenePrincipal"],
        "title": scene_master_data["title"],
        "maxDurationSeconds": scene_master_data["maxDurationSeconds"],
    } in data["scenes"]


def test_get_templates_returns_400_when_no_token(client):
    """Test GET /getTemplates returns 400 when no authorization header."""
    response = client.get("/getTemplates")

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.real_aws
async def test_get_templates_returns_injected_template(
    client,
    auth_headers,
    template_data: dict[str, object],
):
    """Return the template injected for this integration test."""
    response = client.get("/getTemplates", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert {
        "templateId": template_data["templateId"],
        "title": template_data["title"],
        "scenePrincipals": template_data["scenePrincipals"],
    } in data["templates"]


def test_get_projects_returns_400_when_no_token(client):
    """Test GET /getProjects returns 400 when no authorization header."""
    response = client.get("/getProjects")

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.real_aws
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
