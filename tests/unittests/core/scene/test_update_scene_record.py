# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for update_scene_record core logic."""

import base64
from unittest.mock import AsyncMock

import pytest

from recnavi.core.project.scene_urls import SCENE_URL_EXPIRATION_SECONDS
from recnavi.core.scene.update_scene_record import update_scene_record
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientNotFoundError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


BUCKET = "test-bucket"
VIDEO_B64 = base64.b64encode(b"video-bytes").decode()
THUMB_B64 = base64.b64encode(b"thumb-bytes").decode()


def _project_item(video_key: str | None = None) -> dict:
    return {
        "projectId": "proj-123",
        "groupId": "group-456",
        "projectName": "Test Project",
        "ownerUserId": "owner-1",
        "assignedUserIds": ["staff-789"],
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
        "scenes": [
            {
                "sceneId": "scene-1",
                "scenePrincipal": "cooking",
                "status": "reject" if video_key else "not_recorded",
                "videoKey": video_key,
                "thumbnailKey": None,
                "assignedUserIds": ["staff-789"],
            },
        ],
    }


def _staff(user_id: str = "staff-789", group_id: str = "group-456") -> User:
    return User(
        user_id=user_id,
        user_name="Staff User",
        group_id=group_id,
        role=UserRole.STAFF,
    )


async def _update(database, storage, *, scene_id="scene-1", user=None):
    return await update_scene_record(
        projects_db=database,
        storage=storage,
        project_id="proj-123",
        scene_id=scene_id,
        video_base64=VIDEO_B64,
        thumbnail_base64=THUMB_B64,
        user=user or _staff(),
        bucket_name=BUCKET,
    )


@pytest.mark.asyncio
async def test_update_scene_record_uploads_and_marks_scene_pending():
    """Test video and thumbnail are stored and the scene becomes pending."""
    database = MockDatabase(initial_items=[_project_item()])
    storage = MockObjectStorage()

    project = await _update(database, storage)

    scene = project.scenes[0]
    assert scene.status.value == "pending"
    assert scene.created_by == "staff-789"
    keys = [key for _, key in storage.objects]
    video_key = next(key for key in keys if key.endswith(".mp4"))
    thumbnail_key = next(key for key in keys if key.endswith(".jpg"))
    assert storage.objects[(BUCKET, video_key)] == (
        b"video-bytes",
        "video/mp4",
    )
    assert storage.objects[(BUCKET, thumbnail_key)] == (
        b"thumb-bytes",
        "image/jpeg",
    )
    assert video_key.startswith("projects/proj-123/scenes/scene-1/")
    expires = SCENE_URL_EXPIRATION_SECONDS
    assert scene.video_url == f"mock://{BUCKET}/{video_key}?expires={expires}"
    assert scene.thumbnail_url == (
        f"mock://{BUCKET}/{thumbnail_key}?expires={expires}"
    )
    dumped = project.model_dump(by_alias=True, mode="json")
    assert "videoKey" not in dumped["scenes"][0]
    assert "thumbnailKey" not in dumped["scenes"][0]


@pytest.mark.asyncio
async def test_update_scene_record_deletes_the_previous_shot():
    """Test re-recording replaces the old shot with a new one."""
    old_key = "projects/proj-123/scenes/scene-1/old-shot.mp4"
    database = MockDatabase(initial_items=[_project_item(video_key=old_key)])
    storage = MockObjectStorage()
    storage.objects[(BUCKET, old_key)] = (b"old", "video/mp4")
    old_thumb = "projects/proj-123/scenes/scene-1/old-shot_thumb.jpg"
    storage.objects[(BUCKET, old_thumb)] = (b"old", "image/jpeg")

    project = await _update(database, storage)

    new_key = (
        project.scenes[0]
        .video_url.split("?")[0]
        .removeprefix(
            f"mock://{BUCKET}/",
        )
    )
    assert new_key != old_key
    assert {key for _, key in storage.objects} == {
        new_key,
        new_key.replace(".mp4", "_thumb.jpg"),
    }


@pytest.mark.asyncio
async def test_old_shot_is_deleted_only_after_project_is_saved(monkeypatch):
    """Test the prior recording remains until the updated project is saved."""
    old_key = "projects/proj-123/scenes/scene-1/old-shot.mp4"
    database = MockDatabase(initial_items=[_project_item(video_key=old_key)])
    storage = MockObjectStorage()
    events = []
    original_put = database.put_item
    original_delete = storage.delete_object_by_key

    async def put_item(*args, **kwargs):
        events.append("put")
        return await original_put(*args, **kwargs)

    async def delete_object_by_key(*, bucket_name, object_key):
        events.append(("delete", object_key))
        return await original_delete(
            bucket_name=bucket_name,
            object_key=object_key,
        )

    monkeypatch.setattr(database, "put_item", put_item)
    monkeypatch.setattr(
        storage,
        "delete_object_by_key",
        delete_object_by_key,
    )
    storage.objects[(BUCKET, old_key)] = (b"old", "video/mp4")

    await _update(database, storage)

    assert events == [
        "put",
        ("delete", old_key),
        ("delete", old_key.replace(".mp4", "_thumb.jpg")),
    ]


@pytest.mark.asyncio
async def test_partial_upload_failure_cleans_new_objects_and_skips_database_write(
    monkeypatch,
):
    """Test a thumbnail upload failure removes the already uploaded video."""
    database = MockDatabase(initial_items=[_project_item()])
    original_item = database.items[0].copy()
    storage = MockObjectStorage()
    original_upload = storage.upload_base64
    upload_calls = 0

    async def upload_then_fail_thumbnail(**kwargs):
        nonlocal upload_calls
        upload_calls += 1
        if upload_calls == 2:
            raise RuntimeError("thumbnail upload failed")
        await original_upload(**kwargs)

    put_item = AsyncMock(wraps=database.put_item)
    monkeypatch.setattr(storage, "upload_base64", upload_then_fail_thumbnail)
    monkeypatch.setattr(database, "put_item", put_item)

    with pytest.raises(RuntimeError, match="thumbnail upload failed"):
        await _update(database, storage)

    assert storage.objects == {}
    assert database.items[0] == original_item
    put_item.assert_not_awaited()


@pytest.mark.asyncio
async def test_database_conflict_cleans_new_objects_and_keeps_old_shot(
    monkeypatch,
):
    """Test a failed conditional save preserves the prior recording."""
    old_key = "projects/proj-123/scenes/scene-1/old-shot.mp4"
    database = MockDatabase(initial_items=[_project_item(video_key=old_key)])
    original_item = database.items[0].copy()
    storage = MockObjectStorage()
    old_thumb = "projects/proj-123/scenes/scene-1/old-shot_thumb.jpg"
    storage.objects[(BUCKET, old_key)] = (b"old video", "video/mp4")
    storage.objects[(BUCKET, old_thumb)] = (b"old thumb", "image/jpeg")
    put_item = AsyncMock(side_effect=ClientConflictError("version conflict"))
    monkeypatch.setattr(database, "put_item", put_item)

    with pytest.raises(ClientConflictError, match="version conflict"):
        await _update(database, storage)

    assert database.items[0] == original_item
    assert storage.objects == {
        (BUCKET, old_key): (b"old video", "video/mp4"),
        (BUCKET, old_thumb): (b"old thumb", "image/jpeg"),
    }


@pytest.mark.asyncio
async def test_update_scene_record_deletes_nothing_on_first_recording():
    """Test no deletion happens when the scene had no recording."""
    database = MockDatabase(initial_items=[_project_item()])
    storage = MockObjectStorage()
    storage.objects[(BUCKET, "projects/proj-123/other.mp4")] = (
        b"x",
        "video/mp4",
    )

    await _update(database, storage)

    assert (BUCKET, "projects/proj-123/other.mp4") in storage.objects


@pytest.mark.asyncio
async def test_update_scene_record_raises_404_when_project_not_found():
    """Test an unknown project raises ClientNotFoundError."""
    storage = MockObjectStorage()

    with pytest.raises(ClientNotFoundError, match="Project not found"):
        await _update(MockDatabase(), storage)

    assert storage.objects == {}


@pytest.mark.asyncio
async def test_update_scene_record_raises_404_when_scene_not_found():
    """Test an unknown scene raises ClientNotFoundError."""
    storage = MockObjectStorage()
    database = MockDatabase(initial_items=[_project_item()])

    with pytest.raises(ClientNotFoundError, match="Scene not found"):
        await _update(database, storage, scene_id="missing")

    assert storage.objects == {}


@pytest.mark.asyncio
async def test_update_scene_record_raises_403_when_not_assigned():
    """Test a staff member not assigned to the scene is forbidden."""
    storage = MockObjectStorage()
    item = _project_item()
    item["assignedUserIds"].append("staff-other")
    database = MockDatabase(initial_items=[item])

    with pytest.raises(ClientAuthorizationError, match="Not assigned"):
        await _update(database, storage, user=_staff(user_id="staff-other"))

    assert storage.objects == {}


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.OWNER, UserRole.ADMIN])
async def test_update_scene_record_allows_higher_role_to_act_as_staff(role):
    """Test higher-role users can record when assigned to the project."""
    storage = MockObjectStorage()
    database = MockDatabase(initial_items=[_project_item()])
    user = User(
        user_id="staff-789",
        user_name="Not Staff",
        group_id="group-456",
        role=role,
    )

    project = await _update(database, storage, user=user)

    assert project.scenes[0].status.value == "pending"
    assert storage.objects
