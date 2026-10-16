# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for update_project core logic."""

import pytest

from recnavi.core.project.update_project import merge_scenes
from recnavi.core.project.update_project import update_project
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.scene_input import SceneInput
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientNotFoundError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


def make_users_db(*user_ids: str, group_id: str = "group-1") -> MockDatabase:
    """Build a users database holding staff users of the given group."""
    return MockDatabase(
        initial_items=[
            {
                "userId": user_id,
                "userName": user_id,
                "role": "staff",
                "groupId": group_id,
            }
            for user_id in user_ids
        ],
    )


def make_project(*, group_id: str = "group-1") -> Project:
    """Build an existing project owned by the given group."""
    return Project(
        project_id="proj-123",
        group_id=group_id,
        owner_user_id="owner-1",
        project_name="Name",
        description="Description",
        assigned_user_ids=[],
        scenes=[],
        status=ProjectStatus.IN_PROGRESS,
        version=1,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )


def make_owner(*, group_id: str = "group-1") -> User:
    """Build an owner user of the given group."""
    return User(
        user_id="owner-1",
        user_name="Owner User",
        group_id=group_id,
        role=UserRole.OWNER,
    )


def test_merge_scenes_adds_new_scene_when_scene_id_is_null():
    """Test merge_scenes adds new scene with NOT_RECORDED status when scene_id is None."""
    existing_scenes = [
        Scene(
            scene_id="scene-1",
            scene_principal="cooking",
            assigned_user_ids=[],
            status=SceneStatus.NOT_RECORDED,
        ),
    ]
    scene_inputs = [
        SceneInput(
            scene_id="scene-1",
            scene_principal="cooking",
            assigned_user_ids=[],
        ),
        SceneInput(
            scene_principal="eating",
            assigned_user_ids=["user-1"],
        ),
    ]

    merged_scenes = merge_scenes(
        existing_scenes=existing_scenes,
        scene_inputs=scene_inputs,
    )

    assert len(merged_scenes) == 2
    assert merged_scenes[0].scene_id == "scene-1"
    assert merged_scenes[1].scene_id is not None
    assert merged_scenes[1].scene_principal == "eating"
    assert merged_scenes[1].status == SceneStatus.NOT_RECORDED
    assert merged_scenes[1].assigned_user_ids == ["user-1"]


def test_merge_scenes_preserves_recording_state_when_updating_existing_scene():
    """Test merge_scenes preserves status, video_key, etc when updating scene."""
    existing_scenes = [
        Scene(
            scene_id="scene-1",
            scene_principal="cooking",
            assigned_user_ids=["user-old"],
            status=SceneStatus.APPROVE,
            video_key="s3://bucket/video.mp4",
            thumbnail_key="s3://bucket/thumb.jpg",
            created_by="user-123",
            created_at="2026-01-01T00:00:00Z",
        ),
    ]
    scene_inputs = [
        SceneInput(
            scene_id="scene-1",
            scene_principal="cooking-updated",
            assigned_user_ids=["user-new"],
        ),
    ]

    merged_scenes = merge_scenes(
        existing_scenes=existing_scenes,
        scene_inputs=scene_inputs,
    )

    assert len(merged_scenes) == 1
    assert merged_scenes[0].scene_id == "scene-1"
    assert merged_scenes[0].scene_principal == "cooking-updated"
    assert merged_scenes[0].assigned_user_ids == ["user-new"]
    assert merged_scenes[0].status == SceneStatus.APPROVE
    assert merged_scenes[0].video_key == "s3://bucket/video.mp4"
    assert merged_scenes[0].thumbnail_key == "s3://bucket/thumb.jpg"
    assert merged_scenes[0].created_by == "user-123"
    assert merged_scenes[0].created_at == "2026-01-01T00:00:00Z"


def test_merge_scenes_deletes_scene_missing_from_input():
    """Test merge_scenes deletes scene when not present in scene_inputs."""
    existing_scenes = [
        Scene(
            scene_id="scene-1",
            scene_principal="cooking",
            assigned_user_ids=[],
            status=SceneStatus.NOT_RECORDED,
        ),
        Scene(
            scene_id="scene-2",
            scene_principal="eating",
            assigned_user_ids=[],
            status=SceneStatus.NOT_RECORDED,
        ),
    ]
    scene_inputs = [
        SceneInput(
            scene_id="scene-1",
            scene_principal="cooking",
            assigned_user_ids=[],
        ),
    ]

    merged_scenes = merge_scenes(
        existing_scenes=existing_scenes,
        scene_inputs=scene_inputs,
    )

    assert len(merged_scenes) == 1
    assert merged_scenes[0].scene_id == "scene-1"


@pytest.mark.asyncio
async def test_update_project_increments_version():
    """Test update_project increments version from v1 to v2."""
    database = MockDatabase()
    owner = User(
        user_id="owner-1",
        user_name="Owner User",
        group_id="group-1",
        role=UserRole.OWNER,
    )
    existing_project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Old Name",
        description="Old Description",
        assigned_user_ids=[],
        scenes=[],
        status=ProjectStatus.IN_PROGRESS,
        version=1,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    await database.put_item(existing_project.model_dump(by_alias=True))

    updated_project = await update_project(
        storage=MockObjectStorage(bucket_name="bucket"),
        projects_db=database,
        users_db=MockDatabase(),
        project_id="proj-123",
        project_name="New Name",
        description="New Description",
        assigned_user_ids=[],
        scenes=[],
        expected_version=1,
        user=owner,
    )

    assert updated_project.version == 2
    assert updated_project.project_name == "New Name"


@pytest.mark.asyncio
async def test_update_project_raises_conflict_on_version_mismatch():
    """Test update_project raises ClientConflictError when version mismatches."""
    database = MockDatabase()
    owner = User(
        user_id="owner-1",
        user_name="Owner User",
        group_id="group-1",
        role=UserRole.OWNER,
    )
    existing_project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Name",
        description="Description",
        assigned_user_ids=[],
        scenes=[],
        status=ProjectStatus.IN_PROGRESS,
        version=2,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    await database.put_item(existing_project.model_dump(by_alias=True))

    with pytest.raises(ClientConflictError) as exc_info:
        await update_project(
            storage=MockObjectStorage(bucket_name="bucket"),
            projects_db=database,
            users_db=MockDatabase(),
            project_id="proj-123",
            project_name="New Name",
            description="New Description",
            assigned_user_ids=[],
            scenes=[],
            expected_version=1,
            user=owner,
        )

    assert "version mismatch" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_update_project_raises_authorization_error_for_non_owner():
    """Test update_project raises ClientAuthorizationError for non-owner."""
    database = MockDatabase()
    staff = User(
        user_id="staff-1",
        user_name="Staff User",
        group_id="group-1",
        role=UserRole.STAFF,
    )
    existing_project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Name",
        description="Description",
        assigned_user_ids=[],
        scenes=[],
        status=ProjectStatus.IN_PROGRESS,
        version=1,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    await database.put_item(existing_project.model_dump(by_alias=True))

    with pytest.raises(ClientAuthorizationError):
        await update_project(
            storage=MockObjectStorage(bucket_name="bucket"),
            projects_db=database,
            users_db=MockDatabase(),
            project_id="proj-123",
            project_name="New Name",
            description="New Description",
            assigned_user_ids=[],
            scenes=[],
            expected_version=1,
            user=staff,
        )


@pytest.mark.asyncio
async def test_update_project_preserves_video_key_and_recording_state():
    """Test update_project preserves video_key, status, etc when updating scenes."""
    database = MockDatabase()
    owner = User(
        user_id="owner-1",
        user_name="Owner User",
        group_id="group-1",
        role=UserRole.OWNER,
    )
    existing_project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Name",
        description="Description",
        assigned_user_ids=[],
        scenes=[
            Scene(
                scene_id="scene-1",
                scene_principal="cooking",
                assigned_user_ids=[],
                status=SceneStatus.APPROVE,
                video_key="s3://bucket/video.mp4",
                thumbnail_key="s3://bucket/thumb.jpg",
                created_by="staff-1",
                created_at="2026-01-01T00:00:00Z",
            ),
        ],
        status=ProjectStatus.IN_PROGRESS,
        version=1,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    await database.put_item(existing_project.model_dump(by_alias=True))

    updated_project = await update_project(
        storage=MockObjectStorage(bucket_name="bucket"),
        projects_db=database,
        users_db=make_users_db("user-2", "user-3"),
        project_id="proj-123",
        project_name="Updated Name",
        description="Updated Description",
        assigned_user_ids=["user-2"],
        scenes=[
            SceneInput(
                scene_id="scene-1",
                scene_principal="cooking-updated",
                assigned_user_ids=["user-3"],
            ),
        ],
        expected_version=1,
        user=owner,
    )

    assert len(updated_project.scenes) == 1
    scene = updated_project.scenes[0]
    assert scene.scene_id == "scene-1"
    assert scene.scene_principal == "cooking-updated"
    assert scene.assigned_user_ids == ["user-3"]
    assert scene.status == SceneStatus.APPROVE
    assert (
        scene.video_url == "mock://bucket/s3://bucket/video.mp4?expires=3600"
    )
    assert scene.thumbnail_url == (
        "mock://bucket/s3://bucket/thumb.jpg?expires=3600"
    )
    dumped = scene.model_dump(by_alias=True)
    assert "videoKey" not in dumped
    assert "thumbnailKey" not in dumped
    assert scene.created_by == "staff-1"
    assert scene.created_at == "2026-01-01T00:00:00Z"

    stored_project = await database.get_item({"projectId": "proj-123"})
    assert stored_project is not None
    stored_scene = stored_project["scenes"][0]
    assert stored_scene["videoKey"] == "s3://bucket/video.mp4"
    assert stored_scene["thumbnailKey"] == "s3://bucket/thumb.jpg"
    assert "videoUrl" not in stored_scene
    assert "thumbnailUrl" not in stored_scene


@pytest.mark.asyncio
async def test_update_project_raises_not_found_for_missing_project():
    database = MockDatabase()

    with pytest.raises(ClientNotFoundError):
        await update_project(
            projects_db=database,
            users_db=MockDatabase(),
            project_id="missing",
            project_name="Name",
            description="",
            assigned_user_ids=[],
            scenes=[],
            expected_version=0,
            user=User(
                user_id="owner-1",
                user_name="Owner",
                group_id="group-1",
                role=UserRole.OWNER,
            ),
            storage=MockObjectStorage(bucket_name="bucket"),
        )

    assert database.items == []


@pytest.mark.asyncio
async def test_update_project_rejects_owner_of_another_group():
    """Test update_project raises 403 error and keeps DB unchanged for cross-group owner."""
    database = MockDatabase()
    existing_project = make_project(group_id="group-1")
    await database.put_item(existing_project.model_dump(by_alias=True))
    before = [dict(item) for item in database.items]

    with pytest.raises(ClientAuthorizationError):
        await update_project(
            storage=MockObjectStorage(bucket_name="bucket"),
            projects_db=database,
            users_db=MockDatabase(),
            project_id="proj-123",
            project_name="Hacked",
            description="Hacked",
            assigned_user_ids=[],
            scenes=[],
            expected_version=1,
            user=make_owner(group_id="group-2"),
        )

    assert database.items == before


@pytest.mark.asyncio
async def test_update_project_checks_group_before_version():
    """Test cross-group owner gets authorization error even with wrong version."""
    database = MockDatabase()
    await database.put_item(make_project().model_dump(by_alias=True))

    with pytest.raises(ClientAuthorizationError):
        await update_project(
            storage=MockObjectStorage(bucket_name="bucket"),
            projects_db=database,
            users_db=MockDatabase(),
            project_id="proj-123",
            project_name="New Name",
            description="Description",
            assigned_user_ids=[],
            scenes=[],
            expected_version=99,
            user=make_owner(group_id="group-2"),
        )


@pytest.mark.asyncio
async def test_update_project_rejects_unknown_project_assignee():
    """Test update_project rejects project assignee missing from users table."""
    database = MockDatabase()
    await database.put_item(make_project().model_dump(by_alias=True))
    before = [dict(item) for item in database.items]

    with pytest.raises(ClientAuthorizationError):
        await update_project(
            storage=MockObjectStorage(bucket_name="bucket"),
            projects_db=database,
            users_db=make_users_db("user-1"),
            project_id="proj-123",
            project_name="New Name",
            description="Description",
            assigned_user_ids=["ghost"],
            scenes=[],
            expected_version=1,
            user=make_owner(),
        )

    assert database.items == before


@pytest.mark.asyncio
async def test_update_project_rejects_other_group_scene_assignee():
    """Test update_project rejects scene assignee belonging to another group."""
    database = MockDatabase()
    await database.put_item(make_project().model_dump(by_alias=True))
    before = [dict(item) for item in database.items]

    with pytest.raises(ClientAuthorizationError):
        await update_project(
            storage=MockObjectStorage(bucket_name="bucket"),
            projects_db=database,
            users_db=make_users_db("outsider", group_id="group-2"),
            project_id="proj-123",
            project_name="New Name",
            description="Description",
            assigned_user_ids=[],
            scenes=[
                SceneInput(
                    scene_principal="cooking",
                    assigned_user_ids=["outsider"],
                ),
            ],
            expected_version=1,
            user=make_owner(),
        )

    assert database.items == before


@pytest.mark.asyncio
async def test_update_project_accepts_same_group_assignees():
    """Test update_project accepts project and scene assignees of the same group."""
    database = MockDatabase()
    await database.put_item(make_project().model_dump(by_alias=True))

    updated_project = await update_project(
        storage=MockObjectStorage(bucket_name="bucket"),
        projects_db=database,
        users_db=make_users_db("user-1", "user-2"),
        project_id="proj-123",
        project_name="New Name",
        description="Description",
        assigned_user_ids=["user-1"],
        scenes=[
            SceneInput(
                scene_principal="cooking",
                assigned_user_ids=["user-2"],
            ),
        ],
        expected_version=1,
        user=make_owner(),
    )

    assert updated_project.assigned_user_ids == ["user-1"]
    assert updated_project.scenes[0].assigned_user_ids == ["user-2"]


@pytest.mark.asyncio
async def test_update_project_returns_null_urls_for_unrecorded_scene():
    """Test update_project returns null urls for scenes without keys."""
    database = MockDatabase()
    await database.put_item(make_project().model_dump(by_alias=True))

    updated_project = await update_project(
        projects_db=database,
        users_db=make_users_db("user-2"),
        storage=MockObjectStorage(bucket_name="bucket"),
        project_id="proj-123",
        project_name="New Name",
        description="Description",
        assigned_user_ids=[],
        scenes=[
            SceneInput(
                scene_principal="cooking",
                assigned_user_ids=["user-2"],
            ),
        ],
        expected_version=1,
        user=make_owner(),
    )

    assert updated_project.scenes[0].video_url is None
    assert updated_project.scenes[0].thumbnail_url is None
