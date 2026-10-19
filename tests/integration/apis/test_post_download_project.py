# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project download HTTP authorization, policy, and archive contract."""

import base64
import io
import json
import zipfile
from collections.abc import AsyncIterator
from typing import cast
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
import pytest_asyncio

from recnavi.apis.auth.auth import verify_user
from recnavi.config.variables import ENV
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.main import app


@pytest.fixture
def owner_auth():
    """Use an owner identity at the existing HTTP authentication seam."""
    previous = app.dependency_overrides[verify_user]
    app.dependency_overrides[verify_user] = lambda: User(
        user_id="test-user-123",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="it-group",
    )
    try:
        yield
    finally:
        app.dependency_overrides[verify_user] = previous


@pytest_asyncio.fixture
async def downloadable_project() -> AsyncIterator[Project]:
    """Seed public interfaces of shared CI infrastructure and clean every object."""
    if ENV != "CI":
        pytest.skip("Archive integration uses CI in-memory infrastructure")
    database = cast(dict[str, BaseDatabase], app.state.database)[
        PROJECTS_TABLE_NAME
    ]
    storage = cast(BaseObjectStorage, app.state.object_storage)
    project_id = f"it_download_{uuid4().hex}"
    project = Project(
        project_id=project_id,
        project_name="Archive Project",
        description="Archive description",
        owner_user_id="test-user-123",
        group_id="it-group",
        created_at="2026-10-01T00:00:00Z",
        scenes=[
            Scene(
                scene_id=f"scene-{index}",
                scene_principal="cooking",
                status=SceneStatus.APPROVED,
                video_key=f"projects/{project_id}/scenes/scene-{index}/video.mp4",
                created_by="staff",
                created_at="2026-10-01T01:00:00Z",
            )
            for index in range(2)
        ],
    )
    try:
        await database.put_item(project.model_dump(by_alias=True))
        for index, scene in enumerate(project.scenes):
            await storage.upload_base64(
                object_key=cast(str, scene.video_key),
                base64_data=base64.b64encode(
                    f"video-{index}".encode(),
                ).decode(),
            )
        yield project
    finally:
        try:
            await database.delete_item({"projectId": project_id})
        finally:
            await storage.delete_objects_by_prefix(
                prefix=f"projects/{project_id}/",
            )


def test_download_project_returns_400_when_no_token(client):
    response = client.post("/downloadProject", json={"projectId": "unknown"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_download_archive_content_and_expiry(
    client,
    downloadable_project: Project,
    owner_auth,
):
    response = client.post(
        "/downloadProject",
        headers={"Authorization": "Bearer owner_token"},
        json={"projectId": downloadable_project.project_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["expiresInSeconds"] == 3600
    assert "expires=3600" in data["downloadUrl"]
    archive_key = urlsplit(data["downloadUrl"]).path.removeprefix("/")
    assert archive_key.startswith(
        f"projects/{downloadable_project.project_id}/archives/",
    )
    storage = cast(BaseObjectStorage, app.state.object_storage)
    with zipfile.ZipFile(
        io.BytesIO(await storage.download_object(object_key=archive_key)),
    ) as archive:
        assert archive.namelist() == [
            "01_cooking.mp4",
            "02_cooking.mp4",
            "metadata.json",
        ]
        assert archive.read("01_cooking.mp4") == b"video-0"
        assert archive.read("02_cooking.mp4") == b"video-1"
        metadata = json.loads(archive.read("metadata.json"))
    assert metadata["projectName"] == "Archive Project"
    assert metadata["description"] == "Archive description"
    assert metadata["scenes"][0]["createdBy"] == "staff"
    assert metadata["scenes"][0]["createdAt"] == "2026-10-01T01:00:00Z"
    assert metadata["scenes"][0]["sceneId"] == "scene-0"
    assert metadata["scenes"][0]["scenePrincipal"] == "cooking"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "violation",
    ["pending", "different-owner", "different-group"],
)
async def test_download_enforces_project_policy(
    client,
    downloadable_project: Project,
    violation,
    owner_auth,
):
    project = downloadable_project
    if violation == "pending":
        project.scenes[0].status = SceneStatus.PENDING
    elif violation == "different-owner":
        project.owner_user_id = "other-owner"
    else:
        project.group_id = "other-group"
    await app.state.database[PROJECTS_TABLE_NAME].put_item(
        project.model_dump(by_alias=True),
    )
    response = client.post(
        "/downloadProject",
        headers={"Authorization": "Bearer owner_token"},
        json={"projectId": project.project_id},
    )
    assert response.status_code == (400 if violation == "pending" else 403)


@pytest.mark.asyncio
async def test_download_rejects_admin_role(
    client,
    auth_headers,
    downloadable_project: Project,
):
    response = client.post(
        "/downloadProject",
        headers=auth_headers,
        json={"projectId": downloadable_project.project_id},
    )
    assert response.status_code == 403
