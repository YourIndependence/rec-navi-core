# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Archive policy, file naming, and metadata."""

import io
import json
import zipfile

import pytest

from recnavi.core.project.download_project import create_project_archive
from recnavi.core.types.project import Project
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientValueError
from tests.mockups.mock_object_storage import MockObjectStorage


def owner() -> User:
    return User(
        user_id="owner",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group",
    )


def project() -> Project:
    return Project(
        project_id="p",
        project_name="Project",
        description="Description",
        owner_user_id="owner",
        group_id="group",
        created_at="2026-10-01T00:00:00Z",
        scenes=[
            Scene(
                scene_id=f"s{i}",
                scene_principal="cooking",
                status=SceneStatus.APPROVED,
                video_key=f"projects/p/scenes/s{i}/video.mp4",
                created_by="staff",
                created_at="2026-10-01T01:00:00Z",
            )
            for i in range(2)
        ],
    )


@pytest.mark.parametrize(
    ("role", "user_id", "group_id"),
    [
        (UserRole.ADMIN, "other", "group"),
        (UserRole.STAFF, "owner", "group"),
        (UserRole.OWNER, "other", "group"),
    ],
)
@pytest.mark.asyncio
async def test_download_requires_owner_permission(
    role,
    user_id,
    group_id,
):
    user = User(
        user_id=user_id,
        user_name="User",
        role=role,
        group_id=group_id,
    )
    with pytest.raises(ClientAuthorizationError):
        await create_project_archive(
            user=user,
            project=project(),
            storage=MockObjectStorage(bucket_name="media"),
        )


@pytest.mark.parametrize(
    "state",
    ["empty", "pending", "missing", "other-project", "other-scene"],
)
@pytest.mark.asyncio
async def test_download_rejects_incomplete_or_foreign_recordings(state):
    value = project()
    if state == "empty":
        value.scenes = []
    elif state == "pending":
        value.scenes[0].status = SceneStatus.PENDING
    elif state == "missing":
        value.scenes[0].video_key = None
    else:
        value.scenes[0].video_key = (
            "projects/other/scenes/s0/video.mp4"
            if state == "other-project"
            else "projects/p/scenes/other/video.mp4"
        )
    with pytest.raises(ClientValueError):
        await create_project_archive(
            user=owner(),
            project=value,
            storage=MockObjectStorage(bucket_name="media"),
        )


@pytest.mark.asyncio
async def test_archive_preserves_order_metadata_and_unique_download_keys():
    value = project()
    storage = MockObjectStorage(bucket_name="media")
    for index, scene in enumerate(value.scenes):
        storage.objects[("media", scene.video_key)] = (
            f"video-{index}".encode(),
            "video/mp4",
        )
    first = await create_project_archive(
        user=owner(),
        project=value,
        storage=storage,
    )
    first_url = first.download_url
    second = await create_project_archive(
        user=owner(),
        project=value,
        storage=storage,
    )
    assert first_url != second.download_url
    archives = [key for bucket, key in storage.objects if "/archives/" in key]
    assert len(archives) == 2
    assert all(key.startswith("projects/p/archives/") for key in archives)
    with zipfile.ZipFile(
        io.BytesIO(await storage.download_object(object_key=archives[0])),
    ) as archive:
        assert archive.namelist() == [
            "01_cooking.mp4",
            "02_cooking.mp4",
            "metadata.json",
        ]
        assert archive.read("01_cooking.mp4") == b"video-0"
        assert archive.read("02_cooking.mp4") == b"video-1"
        metadata = json.loads(archive.read("metadata.json"))
    assert metadata["projectName"] == "Project"
    assert metadata["description"] == "Description"
    assert metadata["scenes"][0] == {
        "sceneId": "s0",
        "scenePrincipal": "cooking",
        "createdBy": "staff",
        "createdAt": "2026-10-01T01:00:00Z",
        "fileName": "01_cooking.mp4",
    }


@pytest.mark.asyncio
async def test_archive_sanitizes_scene_principal_paths():
    value = project()
    value.scenes[0].scene_principal = "../../evil\\name"
    storage = MockObjectStorage(bucket_name="media")
    for scene in value.scenes:
        storage.objects[("media", scene.video_key)] = (b"video", "video/mp4")
    await create_project_archive(user=owner(), project=value, storage=storage)
    archive_key = next(
        key for bucket, key in storage.objects if "/archives/" in key
    )
    with zipfile.ZipFile(
        io.BytesIO(await storage.download_object(object_key=archive_key)),
    ) as archive:
        assert all(
            "/" not in name and "\\" not in name for name in archive.namelist()
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.OWNER, UserRole.ADMIN])
@pytest.mark.parametrize("group_id", ["group", "other-group"])
async def test_download_allows_owner_permission(role, group_id):
    value = project()
    storage = MockObjectStorage(bucket_name="media")
    for scene in value.scenes:
        storage.objects[("media", scene.video_key)] = (b"video", "video/mp4")
    user = owner().model_copy(update={"role": role, "group_id": group_id})
    result = await create_project_archive(
        user=user,
        project=value,
        storage=storage,
    )
    assert result is value
    assert result.download_url
