# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Submission rules, authorization, persistence, and concurrent updates."""

from unittest.mock import AsyncMock

import pytest

from recnavi.core.project.submit_project import submit_project
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.fixture
def project() -> Project:
    return Project(
        project_id="project-1",
        project_name="Shooting",
        group_id="group-1",
        owner_user_id="owner-1",
        assigned_user_ids=["staff-1"],
        created_at="2026-01-01T00:00:00Z",
        version=4,
        scenes=[
            Scene(
                scene_id="scene-1",
                scene_principal="intro",
                status=SceneStatus.PENDING,
                video_key="video.mp4",
                thumbnail_key="thumb.jpg",
            ),
        ],
    )


@pytest.fixture
def user() -> User:
    return User(
        user_id="staff-1",
        user_name="Staff",
        role=UserRole.STAFF,
        group_id="group-1",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("version", [None, 0, 4])
async def test_submission_advances_version_and_returns_public_urls(
    project,
    user,
    version,
):
    item = project.model_dump(by_alias=True)
    if version is None:
        item.pop("version")
    else:
        item["version"] = version
    db = MockDatabase(initial_items=[item])
    result, missing = await submit_project(
        projects_db=db,
        storage=MockObjectStorage(bucket_name="media"),
        project_id=project.project_id,
        user=user,
    )
    assert missing == []
    assert result.status == ProjectStatus.SUBMITTED
    assert result.version == (version or 0) + 1
    assert result.updated_at is not None
    public_scene = result.model_dump(by_alias=True)["scenes"][0]
    assert public_scene["videoUrl"].startswith("mock://media/video.mp4?")
    assert public_scene["thumbnailUrl"].startswith("mock://media/thumb.jpg?")
    assert "videoKey" not in public_scene
    assert "thumbnailKey" not in public_scene
    stored = await db.get_item({"projectId": project.project_id})
    assert stored["version"] == result.version
    assert stored["status"] == "submitted"
    assert stored["scenes"][0]["videoKey"] == "video.mp4"
    assert "videoUrl" not in stored["scenes"][0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,video,missing",
    [
        (SceneStatus.PENDING, "video.mp4", []),
        (SceneStatus.APPROVED, "video.mp4", []),
        (SceneStatus.REJECTED, "video.mp4", ["scene-1"]),
        (SceneStatus.NOT_RECORDED, "video.mp4", ["scene-1"]),
        (SceneStatus.PENDING, None, ["scene-1"]),
        (SceneStatus.APPROVED, "", ["scene-1"]),
    ],
)
async def test_submission_reports_incomplete_scenes_without_writing(
    project,
    user,
    status,
    video,
    missing,
):
    project.scenes[0].status = status
    project.scenes[0].video_key = video
    original = project.model_dump(by_alias=True)
    db = MockDatabase(initial_items=[original])
    result, actual_missing = await submit_project(
        projects_db=db,
        storage=MockObjectStorage(bucket_name="media"),
        project_id=project.project_id,
        user=user,
    )
    assert actual_missing == missing
    if missing:
        assert result.status == ProjectStatus.IN_PROGRESS
        assert await db.get_item({"projectId": project.project_id}) == original


@pytest.mark.asyncio
async def test_submission_retry_is_idempotent(project, user):
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    storage = MockObjectStorage(bucket_name="media")
    first = await submit_project(
        projects_db=db,
        storage=storage,
        project_id=project.project_id,
        user=user,
    )
    second = await submit_project(
        projects_db=db,
        storage=storage,
        project_id=project.project_id,
        user=user,
    )
    assert first == second
    assert second[0].version == 5


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role,group,user_id",
    [
        (UserRole.OWNER, "group-1", "staff-1"),
        (UserRole.ADMIN, "group-1", "staff-1"),
        (UserRole.STAFF, "other-group", "staff-1"),
        (UserRole.STAFF, "group-1", "unassigned"),
    ],
)
async def test_submission_rejects_unauthorized_users(
    project,
    role,
    group,
    user_id,
):
    original = project.model_dump(by_alias=True)
    db = MockDatabase(initial_items=[original])
    user = User(user_id=user_id, user_name="Caller", role=role, group_id=group)
    with pytest.raises(ClientAuthorizationError):
        await submit_project(
            projects_db=db,
            storage=MockObjectStorage(bucket_name="media"),
            project_id=project.project_id,
            user=user,
        )
    assert await db.get_item({"projectId": project.project_id}) == original


@pytest.mark.asyncio
async def test_submission_rejects_empty_project(project, user):
    project.scenes = []
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    with pytest.raises(ClientUnprocessableEntityError):
        await submit_project(
            projects_db=db,
            storage=MockObjectStorage(bucket_name="media"),
            project_id=project.project_id,
            user=user,
        )


@pytest.mark.asyncio
async def test_submission_rejects_missing_project(user):
    with pytest.raises(ClientNotFoundError):
        await submit_project(
            projects_db=MockDatabase(),
            storage=MockObjectStorage(bucket_name="media"),
            project_id="missing",
            user=user,
        )


@pytest.mark.asyncio
async def test_submission_does_not_overwrite_concurrent_scene_edit(
    project,
    user,
):
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    original_put = db.put_item

    async def concurrent_put(*args, **kwargs):
        db.items[0] = {
            **db.items[0],
            "version": 5,
            "description": "Concurrent edit",
        }
        await original_put(*args, **kwargs)

    db.put_item = concurrent_put
    with pytest.raises(ClientConflictError):
        await submit_project(
            projects_db=db,
            storage=MockObjectStorage(bucket_name="media"),
            project_id=project.project_id,
            user=user,
        )
    stored = await db.get_item({"projectId": project.project_id})
    assert stored["status"] == "in_progress"
    assert stored["description"] == "Concurrent edit"


@pytest.mark.asyncio
async def test_submission_propagates_database_failure(project, user):
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    db.put_item = AsyncMock(side_effect=RuntimeError("Database unavailable"))
    with pytest.raises(RuntimeError, match="Database unavailable"):
        await submit_project(
            projects_db=db,
            storage=MockObjectStorage(bucket_name="media"),
            project_id=project.project_id,
            user=user,
        )


@pytest.mark.asyncio
async def test_concurrent_submission_returns_committed_result(project, user):
    """Two submissions of the same complete version both succeed."""
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    original_put = db.put_item

    async def submit_first(*args, **kwargs):
        db.items[0] = {**db.items[0], "version": 5, "status": "submitted"}
        await original_put(*args, **kwargs)

    db.put_item = submit_first
    result, missing = await submit_project(
        projects_db=db,
        storage=MockObjectStorage(bucket_name="media"),
        project_id=project.project_id,
        user=user,
    )
    assert result.status == ProjectStatus.SUBMITTED
    assert result.version == 5
    assert missing == []
