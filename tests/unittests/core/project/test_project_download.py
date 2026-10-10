# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for project download validation logic."""

import io
import json
import zipfile

import pytest

from recnavi.core.project.project_download import create_project_archive
from recnavi.core.project.project_download import validate_project_for_download
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_object_storage import MockObjectStorage


def test_validate_project_for_download_succeeds_for_owner_with_all_approved():
    """Test validation passes for owner when all scenes are approved."""
    owner = User(
        user_id="owner-1",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group-1",
    )

    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        description="Test Description",
        assigned_user_ids=["staff-1"],
        scenes=[
            Scene(
                scene_id="scene-1",
                scene_principal="cooking",
                status=SceneStatus.APPROVE,
                video_key="projects/proj-123/scenes/scene-1/shot-1.mp4",
                thumbnail_key="projects/proj-123/scenes/scene-1/shot-1_thumb.jpg",
                created_by="staff-1",
                created_at="2026-09-20T10:00:00Z",
                assigned_user_ids=["staff-1"],
            ),
            Scene(
                scene_id="scene-2",
                scene_principal="plating",
                status=SceneStatus.APPROVE,
                video_key="projects/proj-123/scenes/scene-2/shot-2.mp4",
                thumbnail_key="projects/proj-123/scenes/scene-2/shot-2_thumb.jpg",
                created_by="staff-1",
                created_at="2026-09-20T10:05:00Z",
                assigned_user_ids=["staff-1"],
            ),
        ],
        status=ProjectStatus.SUBMITTED,
        version=0,
        created_at="2026-09-20T09:00:00Z",
        updated_at="2026-09-20T10:10:00Z",
    )

    # Should not raise
    validate_project_for_download(user=owner, project=project)


def test_validate_project_for_download_raises_403_for_staff():
    """Test validation raises 403 for staff users."""
    staff = User(
        user_id="staff-1",
        user_name="Staff",
        role=UserRole.STAFF,
        group_id="group-1",
    )

    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        description="Test Description",
        assigned_user_ids=["staff-1"],
        scenes=[],
        status=ProjectStatus.SUBMITTED,
        version=0,
        created_at="2026-09-20T09:00:00Z",
        updated_at="2026-09-20T10:10:00Z",
    )

    with pytest.raises(ClientAuthorizationError):
        validate_project_for_download(user=staff, project=project)


def test_validate_project_for_download_raises_403_for_wrong_group():
    """Test validation raises 403 for users from different group."""
    owner = User(
        user_id="owner-1",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group-2",  # Different group
    )

    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        description="Test Description",
        assigned_user_ids=["staff-1"],
        scenes=[],
        status=ProjectStatus.SUBMITTED,
        version=0,
        created_at="2026-09-20T09:00:00Z",
        updated_at="2026-09-20T10:10:00Z",
    )

    with pytest.raises(ClientAuthorizationError):
        validate_project_for_download(user=owner, project=project)


def test_validate_project_for_download_raises_422_for_not_all_approved():
    """Test validation raises 422 when not all scenes are approved."""
    owner = User(
        user_id="owner-1",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group-1",
    )

    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        description="Test Description",
        assigned_user_ids=["staff-1"],
        scenes=[
            Scene(
                scene_id="scene-1",
                scene_principal="cooking",
                status=SceneStatus.APPROVE,
                video_key="projects/proj-123/scenes/scene-1/shot-1.mp4",
                thumbnail_key="projects/proj-123/scenes/scene-1/shot-1_thumb.jpg",
                created_by="staff-1",
                created_at="2026-09-20T10:00:00Z",
                assigned_user_ids=["staff-1"],
            ),
            Scene(
                scene_id="scene-2",
                scene_principal="plating",
                status=SceneStatus.PENDING,  # Not approved
                video_key="projects/proj-123/scenes/scene-2/shot-2.mp4",
                thumbnail_key="projects/proj-123/scenes/scene-2/shot-2_thumb.jpg",
                created_by="staff-1",
                created_at="2026-09-20T10:05:00Z",
                assigned_user_ids=["staff-1"],
            ),
        ],
        status=ProjectStatus.IN_PROGRESS,
        version=0,
        created_at="2026-09-20T09:00:00Z",
        updated_at="2026-09-20T10:10:00Z",
    )

    with pytest.raises(ClientUnprocessableEntityError):
        validate_project_for_download(user=owner, project=project)


def test_validate_project_for_download_raises_422_for_empty_scenes():
    """Test validation raises 422 when project has no scenes."""
    owner = User(
        user_id="owner-1",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group-1",
    )

    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        description="Test Description",
        assigned_user_ids=["staff-1"],
        scenes=[],  # Empty
        status=ProjectStatus.IN_PROGRESS,
        version=0,
        created_at="2026-09-20T09:00:00Z",
        updated_at="2026-09-20T10:10:00Z",
    )

    with pytest.raises(ClientUnprocessableEntityError):
        validate_project_for_download(user=owner, project=project)


def _approved_scene(scene_id: str, principal: str, video_key: str) -> Scene:
    return Scene(
        scene_id=scene_id,
        scene_principal=principal,
        status=SceneStatus.APPROVE,
        video_key=video_key,
        thumbnail_key=None,
        created_by="staff-1",
        created_at="2026-09-20T10:00:00Z",
        assigned_user_ids=["staff-1"],
    )


def _owner() -> User:
    return User(
        user_id="owner-1",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group-1",
    )


def _project(project_id: str, scenes: list[Scene]) -> Project:
    return Project(
        project_id=project_id,
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        description="Test Description",
        assigned_user_ids=["staff-1"],
        scenes=scenes,
        status=ProjectStatus.SUBMITTED,
        version=0,
        created_at="2026-09-20T09:00:00Z",
        updated_at="2026-09-20T10:10:00Z",
    )


@pytest.mark.asyncio
async def test_create_project_archive_creates_zip_with_videos_and_metadata():
    """Test archive contains videos and metadata.json and is uploaded."""
    storage = MockObjectStorage()
    storage.objects[("test-bucket", "v/1.mp4")] = (
        b"fake video data 1",
        "video/mp4",
    )
    storage.objects[("test-bucket", "v/2.mp4")] = (
        b"fake video data 2",
        "video/mp4",
    )
    project = _project(
        "proj-123",
        [
            _approved_scene("scene-1", "cooking", "v/1.mp4"),
            _approved_scene("scene-2", "plating", "v/2.mp4"),
        ],
    )

    url = await create_project_archive(
        user=_owner(),
        project=project,
        bucket_name="test-bucket",
        storage=storage,
    )

    assert url == "mock://test-bucket/archives/proj-123.zip?expires=3600"
    zip_bytes, content_type = storage.objects[
        ("test-bucket", "archives/proj-123.zip")
    ]
    assert content_type == "application/zip"
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        assert set(zf.namelist()) == {
            "cooking.mp4",
            "plating.mp4",
            "metadata.json",
        }
        assert zf.read("cooking.mp4") == b"fake video data 1"
        assert zf.read("plating.mp4") == b"fake video data 2"
        metadata = json.loads(zf.read("metadata.json").decode("utf-8"))
    assert metadata["projectId"] == "proj-123"
    assert metadata["projectName"] == "Test Project"
    assert metadata["description"] == "Test Description"
    assert metadata["scenes"] == [
        {
            "sceneId": "scene-1",
            "scenePrincipal": "cooking",
            "fileName": "cooking.mp4",
        },
        {
            "sceneId": "scene-2",
            "scenePrincipal": "plating",
            "fileName": "plating.mp4",
        },
    ]


@pytest.mark.asyncio
async def test_create_project_archive_handles_duplicate_scene_principals():
    """Test duplicate scene principals get unique file names."""
    storage = MockObjectStorage()
    scenes = []
    for i in range(1, 4):
        key = f"v/{i}.mp4"
        storage.objects[("test-bucket", key)] = (
            f"video {i}".encode(),
            "video/mp4",
        )
        scenes.append(_approved_scene(f"scene-{i}", "cooking", key))

    await create_project_archive(
        user=_owner(),
        project=_project("proj-456", scenes),
        bucket_name="test-bucket",
        storage=storage,
    )

    zip_bytes, _ = storage.objects[("test-bucket", "archives/proj-456.zip")]
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        assert set(zf.namelist()) == {
            "cooking.mp4",
            "cooking_2.mp4",
            "cooking_3.mp4",
            "metadata.json",
        }
        assert zf.read("cooking_2.mp4") == b"video 2"
        metadata = json.loads(zf.read("metadata.json").decode("utf-8"))
    assert [s["fileName"] for s in metadata["scenes"]] == [
        "cooking.mp4",
        "cooking_2.mp4",
        "cooking_3.mp4",
    ]


@pytest.mark.asyncio
async def test_create_project_archive_raises_403_for_staff():
    """Test validation still runs before touching storage."""
    storage = MockObjectStorage()
    staff = User(
        user_id="staff-1",
        user_name="Staff",
        role=UserRole.STAFF,
        group_id="group-1",
    )

    with pytest.raises(ClientAuthorizationError):
        await create_project_archive(
            user=staff,
            project=_project("p", [_approved_scene("s", "a", "v.mp4")]),
            bucket_name="test-bucket",
            storage=storage,
        )

    assert storage.objects == {}
