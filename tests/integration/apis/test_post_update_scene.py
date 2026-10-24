# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /updateScene endpoint."""

import base64
import time
from collections.abc import AsyncIterator
from typing import cast
from urllib.parse import parse_qs
from urllib.parse import unquote
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from recnavi.config.variables import ENV
from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.scene import SCENE_URL_EXPIRATION_SECONDS
from recnavi.core.types.scene import Scene
from recnavi.main import app


def test_update_scene_returns_401_when_no_token(client):
    """Test POST /updateScene returns 401 when no authorization header."""
    response = client.post(
        "/updateScene",
        json={
            "projectId": "proj-123",
            "sceneId": "scene-456",
            "video": "ZmFrZSB2aWRlbyBkYXRh",
            "thumbnail": "ZmFrZSB0aHVtYm5haWw=",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


@pytest_asyncio.fixture
async def recording_project(
    request: pytest.FixtureRequest,
) -> AsyncIterator[Project]:
    """Seed a project and remove its objects and database item after the test."""
    database = cast(BaseDatabase, app.state.database[PROJECTS_TABLE_NAME])
    storage = cast(BaseObjectStorage, app.state.object_storage)
    project = Project(
        project_id=f"it_recording_{uuid4().hex}",
        group_id="it-group",
        project_name="Test Project",
        owner_user_id="test-user-123",
        created_at="2026-01-01T00:00:00Z",
        assigned_user_ids=["test-user-123"],
        version=request.param or 0,
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                assigned_user_ids=["test-user-123"],
            ),
            Scene(scene_id="untouched", scene_principal="opening"),
        ],
    )
    item = project.to_storage_item()
    if request.param is None:
        item.pop("version")
    await database.put_item(item)
    try:
        yield project
    finally:
        try:
            await storage.delete_objects_by_prefix(
                prefix=f"projects/{project.project_id}/",
            )
        finally:
            await database.delete_item({"projectId": project.project_id})


@pytest.mark.asyncio
@pytest.mark.parametrize("recording_project", [None, 0, 4], indirect=True)
async def test_update_scene_persists_recording_through_http(
    client: TestClient,
    auth_headers: dict[str, str],
    recording_project: Project,
) -> None:
    """Exercise HTTP, use case, domain logic, persistence, and URL serialization."""
    request_started_at = int(time.time())
    response = client.post(
        "/updateScene",
        headers=auth_headers,
        json={
            "projectId": recording_project.project_id,
            "sceneId": "scene-456",
            "video": base64.b64encode(b"video-bytes").decode(),
            "thumbnail": base64.b64encode(b"thumbnail-bytes").decode(),
        },
    )
    request_finished_at = int(time.time())
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    project = data["project"]
    database = cast(BaseDatabase, app.state.database[PROJECTS_TABLE_NAME])
    storage = cast(BaseObjectStorage, app.state.object_storage)
    stored = await database.get_item(
        {"projectId": recording_project.project_id},
    )
    assert stored is not None
    assert (
        stored["version"]
        == project["version"]
        == recording_project.version + 1
    )
    assert stored["updatedAt"] == project["updatedAt"]
    assert stored["updatedAt"] != recording_project.updated_at
    assert stored["scenes"][1] == recording_project.scenes[1].to_storage_item()
    scene = stored["scenes"][0]
    public_scene = project["scenes"][0]
    assert scene["status"] == public_scene["status"] == "pending"
    assert scene["createdBy"] == public_scene["createdBy"] == "test-user-123"
    assert scene["createdAt"] == public_scene["createdAt"]
    assert scene["createdAt"] is not None
    for key_field, url_field, content in (
        ("videoKey", "videoUrl", b"video-bytes"),
        ("thumbnailKey", "thumbnailUrl", b"thumbnail-bytes"),
    ):
        assert scene[key_field].startswith(
            f"projects/{recording_project.project_id}/scenes/scene-456/",
        )
        assert (
            await storage.download_object(object_key=scene[key_field])
            == content
        )
        url = urlsplit(public_scene[url_field])
        path = unquote(url.path)
        assert path.endswith(f"/{scene[key_field]}")
        query = parse_qs(url.query)
        if ENV == "CI":
            assert url.scheme == "mock"
            assert url.hostname == MEDIA_BUCKET_NAME
            assert query["expires"] == [str(SCENE_URL_EXPIRATION_SECONDS)]
        else:
            assert url.scheme in ("https", "http")
            assert url.hostname is not None
            assert url.hostname.startswith(
                f"{MEDIA_BUCKET_NAME}.",
            ) or path.startswith(f"/{MEDIA_BUCKET_NAME}/")
            if "X-Amz-Expires" in query:
                assert query["X-Amz-Expires"] == [
                    str(SCENE_URL_EXPIRATION_SECONDS),
                ]
                assert query["X-Amz-Signature"][0]
            else:
                assert (
                    request_started_at + SCENE_URL_EXPIRATION_SECONDS
                    <= int(query["Expires"][0])
                    <= request_finished_at + SCENE_URL_EXPIRATION_SECONDS
                )
                assert query["Signature"][0]
        assert key_field not in public_scene


@pytest.mark.asyncio
@pytest.mark.parametrize("recording_project", [0], indirect=True)
async def test_rerecording_replaces_persisted_shot_through_http(
    client: TestClient,
    auth_headers: dict[str, str],
    recording_project: Project,
) -> None:
    """Record twice through HTTP and remove only the previous shot."""
    payload = {
        "projectId": recording_project.project_id,
        "sceneId": "scene-456",
        "video": "b2xk",
        "thumbnail": "b2xk",
    }
    response = client.post(
        "/updateScene",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 200
    database = cast(BaseDatabase, app.state.database[PROJECTS_TABLE_NAME])
    storage = cast(BaseObjectStorage, app.state.object_storage)
    first = await database.get_item(
        {"projectId": recording_project.project_id},
    )
    assert first is not None
    old_scene = first["scenes"][0]
    payload.update(video="bmV3", thumbnail="bmV3")
    response = client.post(
        "/updateScene",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 200
    saved = await database.get_item(
        {"projectId": recording_project.project_id},
    )
    assert saved is not None
    assert saved["version"] == response.json()["project"]["version"] == 2
    for key_field in ("videoKey", "thumbnailKey"):
        assert saved["scenes"][0][key_field] != old_scene[key_field]
        assert (
            await storage.download_object(
                object_key=saved["scenes"][0][key_field],
            )
            == b"new"
        )
    old_prefix = old_scene["videoKey"].removesuffix(".mp4")
    assert await storage.delete_objects_by_prefix(prefix=old_prefix) == 0
    assert saved["scenes"][1] == first["scenes"][1]
