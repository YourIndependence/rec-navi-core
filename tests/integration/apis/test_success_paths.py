# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Success-path integration tests over HTTP for every endpoint on dev.

Run with ENV=CI so the in-memory tables are injected. Role mismatches
currently surface as a client error (HTTP 400, status "error"), because
ClientPermissionError is mapped to 400 by the error handler.

Endpoints still in open PRs should add their success tests here with the
same ``as_user`` / ``databases`` helpers once merged.
"""

import base64
import json
import warnings
from collections.abc import AsyncIterator
from collections.abc import Callable
from uuid import uuid4

import pytest
import pytest_asyncio

from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.main import app


GROUP = "it-group"
OTHER_GROUP = "other-group"
PROJECT_KEYS = {
    "projectId",
    "projectName",
    "description",
    "status",
    "scenes",
    "ownerUserId",
    "assignedUserIds",
    "groupId",
    "createdAt",
    "updatedAt",
    "version",
}


def make_project(
    *,
    owner: str = "owner-1",
    assigned: list[str] | None = None,
    group_id: str = GROUP,
    created_at: str = "2026-09-21T00:00:00Z",
) -> dict[str, object]:
    return {
        "projectId": f"it_{uuid4()}",
        "groupId": group_id,
        "projectName": "Integration Test Project",
        "description": "Test project",
        "ownerUserId": owner,
        "assignedUserIds": assigned or [],
        "createdAt": created_at,
        "updatedAt": created_at,
        "status": "in_progress",
        "version": 0,
        "scenes": [
            {
                "sceneId": f"scene_{uuid4()}",
                "scenePrincipal": "cooking",
                "status": "not_recorded",
                "videoKey": None,
                "thumbnailKey": None,
                "createdBy": None,
                "createdAt": None,
                "assignedAt": None,
                "assignedUserIds": [],
            },
        ],
    }


@pytest_asyncio.fixture
async def seed_project(
    databases: dict[str, BaseDatabase],
) -> AsyncIterator[Callable[..., object]]:
    """Seed projects into the mock table and remove them afterwards."""
    db = databases[PROJECTS_TABLE_NAME]
    created: list[dict[str, object]] = []

    async def _seed(**kwargs) -> dict[str, object]:
        item = make_project(**kwargs)
        await db.put_item(item)
        created.append(item)
        return item

    try:
        yield _seed
    finally:
        for item in created:
            await db.delete_item({"projectId": item["projectId"]})


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_greeting_returns_ok_without_token(client):
    response = client.get("/greeting")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert isinstance(data["timestamp"], int)
    assert "environment" in data


@pytest.mark.parametrize(
    "role",
    [UserRole.OWNER, UserRole.STAFF, UserRole.ADMIN],
)
def test_get_me_returns_user_for_each_role(
    client,
    auth_headers,
    as_user: Callable[..., User],
    role: UserRole,
):
    as_user(role, OTHER_GROUP, "u-42")

    response = client.get("/getMe", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["user"]["userId"] == "u-42"
    assert data["user"]["groupId"] == OTHER_GROUP
    assert data["user"]["role"] == role.value
    assert "userName" in data["user"]


@pytest_asyncio.fixture
async def scene_master(
    databases: dict[str, BaseDatabase],
) -> AsyncIterator[dict[str, object]]:
    db = databases[SCENES_TABLE_NAME]
    item = {
        "scenePrincipal": f"it_{uuid4()}",
        "title": "Integration Test Scene",
        "thumbnailUri": "s3://it-test/thumbnail.jpg",
        "guideUri": "s3://it-test/guide.png",
        "maxDurationSeconds": 30,
    }
    await db.put_item(item)
    try:
        yield item
    finally:
        await db.delete_item({"scenePrincipal": item["scenePrincipal"]})


@pytest.mark.asyncio
async def test_get_scene_masters_returns_seeded_scene(
    client,
    auth_headers,
    scene_master: dict[str, object],
):
    response = client.get("/getSceneMasters", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert {
        "scenePrincipal": scene_master["scenePrincipal"],
        "title": "Integration Test Scene",
        "maxDurationSeconds": 30,
    } in data["scenes"]


@pytest_asyncio.fixture
async def template(
    databases: dict[str, BaseDatabase],
) -> AsyncIterator[dict[str, object]]:
    db = databases[TEMPLATES_TABLE_NAME]
    item = {
        "templateId": f"it_{uuid4()}",
        "title": "Integration Test Template",
        "scenePrincipals": ["cooking", "exterior"],
        "thumbnailUri": "s3://it-test/template.jpg",
    }
    await db.put_item(item)
    try:
        yield item
    finally:
        await db.delete_item({"templateId": item["templateId"]})


@pytest.mark.asyncio
async def test_get_templates_returns_seeded_template(
    client,
    auth_headers,
    template: dict[str, object],
):
    response = client.get("/getTemplates", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert {
        "templateId": template["templateId"],
        "title": "Integration Test Template",
        "scenePrincipals": ["cooking", "exterior"],
    } in data["templates"]


@pytest.mark.asyncio
async def test_get_projects_returns_own_projects_only(
    client,
    auth_headers,
    as_user: Callable[..., User],
    seed_project,
):
    mine = await seed_project(owner="owner-1")
    assigned = await seed_project(owner="owner-2", assigned=["owner-1"])
    not_mine = await seed_project(owner="owner-2")
    other_group = await seed_project(owner="owner-1", group_id=OTHER_GROUP)
    as_user(UserRole.OWNER, GROUP, "owner-1")

    response = client.get("/getProjects", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    ids = {p["projectId"] for p in data["projects"]}
    assert {mine["projectId"], assigned["projectId"]} <= ids
    assert not_mine["projectId"] not in ids
    assert other_group["projectId"] not in ids
    assert set(data["projects"][0]) == PROJECT_KEYS
    assert data["nextCursor"] is None


@pytest.mark.asyncio
async def test_get_projects_paginates_with_cursor(
    client,
    auth_headers,
    as_user: Callable[..., User],
    seed_project,
):
    first = await seed_project(
        owner="pager",
        group_id="pager-group",
        created_at="2026-09-01T00:00:00Z",
    )
    second = await seed_project(
        owner="pager",
        group_id="pager-group",
        created_at="2026-09-02T00:00:00Z",
    )
    as_user(UserRole.OWNER, "pager-group", "pager")

    page1 = client.get("/getProjects?limit=1", headers=auth_headers).json()
    assert [p["projectId"] for p in page1["projects"]] == [first["projectId"]]
    assert page1["nextCursor"] is not None
    json.loads(base64.b64decode(page1["nextCursor"]))  # opaque but valid

    page2 = client.get(
        "/getProjects",
        params={"limit": 1, "cursor": page1["nextCursor"]},
        headers=auth_headers,
    ).json()
    assert [p["projectId"] for p in page2["projects"]] == [
        second["projectId"],
    ]
    assert page2["nextCursor"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("role", "user_id"),
    [(UserRole.OWNER, "owner-1"), (UserRole.STAFF, "staff-1")],
)
async def test_get_project_returns_project_for_owner_and_assigned_staff(
    client,
    auth_headers,
    as_user: Callable[..., User],
    seed_project,
    role: UserRole,
    user_id: str,
):
    project = await seed_project(owner="owner-1", assigned=["staff-1"])
    as_user(role, GROUP, user_id)

    response = client.post(
        "/getProject",
        headers=auth_headers,
        json={"projectId": project["projectId"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert set(data["project"]) == PROJECT_KEYS
    assert data["project"]["projectId"] == project["projectId"]
    assert data["project"]["scenes"][0]["scenePrincipal"] == "cooking"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("group_id", "user_id"),
    [(OTHER_GROUP, "owner-1"), (GROUP, "stranger")],
)
async def test_get_project_rejects_tenant_or_membership_mismatch(
    client,
    auth_headers,
    as_user: Callable[..., User],
    seed_project,
    group_id: str,
    user_id: str,
):
    project = await seed_project(owner="owner-1")
    as_user(UserRole.OWNER, group_id, user_id)

    response = client.post(
        "/getProject",
        headers=auth_headers,
        json={"projectId": project["projectId"]},
    )

    assert response.status_code == 400
    assert response.json()["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.OWNER, UserRole.ADMIN])
async def test_create_project_persists_project_for_owner_and_admin(
    client,
    auth_headers,
    as_user: Callable[..., User],
    databases: dict[str, BaseDatabase],
    role: UserRole,
):
    as_user(role, GROUP, "creator-1")
    db = databases[PROJECTS_TABLE_NAME]
    project_id = None
    try:
        response = client.post(
            "/createProject",
            headers=auth_headers,
            json={
                "projectName": "Created via HTTP",
                "description": "d",
                "scenePrincipals": ["cooking", "exterior"],
                "assignedUserIds": ["staff-1"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        project = data["project"]
        project_id = project["projectId"]
        assert set(project) == PROJECT_KEYS
        assert project["ownerUserId"] == "creator-1"
        assert project["groupId"] == GROUP
        assert project["status"] == "in_progress"
        assert [s["scenePrincipal"] for s in project["scenes"]] == [
            "cooking",
            "exterior",
        ]
        assert await db.get_item({"projectId": project_id}) is not None
    finally:
        if project_id:
            await db.delete_item({"projectId": project_id})


def test_create_project_rejects_staff(
    client,
    auth_headers,
    as_user: Callable[..., User],
    databases: dict[str, BaseDatabase],
):
    as_user(UserRole.STAFF, GROUP, "staff-1")
    before = len(databases[PROJECTS_TABLE_NAME].items)

    response = client.post(
        "/createProject",
        headers=auth_headers,
        json={
            "projectName": "Nope",
            "scenePrincipals": ["cooking"],
        },
    )

    assert response.status_code == 400
    assert response.json()["status"] == "error"
    assert len(databases[PROJECTS_TABLE_NAME].items) == before


def test_openapi_json_is_generated(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["paths"]
    for path in (
        "/health",
        "/greeting",
        "/getMe",
        "/getProject",
        "/createProject",
    ):
        assert path in schema["paths"]


@pytest.mark.xfail(
    strict=False,
    reason=(
        "GET /getProjects is registered by both cms_router and pub_router, "
        "producing a duplicate operationId; routing is fixed in another PR."
    ),
)
def test_openapi_operation_ids_are_unique(client):
    # openapi.json merges duplicate routes into one path item, so the
    # duplicates are only visible as a FastAPI warning during generation.
    app.openapi_schema = None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        app.openapi()
    duplicates = [
        str(w.message)
        for w in caught
        if "Duplicate Operation ID" in str(w.message)
    ]

    assert not duplicates, f"duplicate operationIds: {duplicates}"
