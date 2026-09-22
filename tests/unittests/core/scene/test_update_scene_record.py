# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for update_scene_record core logic."""

import pytest

from recnavi.core.scene.update_scene_record import update_scene_record
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_update_scene_record_returns_shot_id_and_keys():
    """Test update_scene_record returns necessary data for S3 upload."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-123",
                "groupId": "group-456",
                "projectName": "Test Project",
                "ownerUserId": "owner-1",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-1",
                        "scenePrincipal": "cooking",
                        "status": "not_recorded",
                        "videoKey": None,
                        "thumbnailKey": None,
                        "assignedUserIds": ["staff-789"],
                    },
                ],
            },
        ],
    )

    staff = User(
        user_id="staff-789",
        user_name="Staff User",
        group_id="group-456",
        role=UserRole.STAFF,
    )

    (
        project,
        scene_index,
        shot_id,
        new_video_key,
        old_video_key,
    ) = await update_scene_record(
        projects_db=database,
        project_id="proj-123",
        scene_id="scene-1",
        user=staff,
    )

    assert project.project_id == "proj-123"
    assert scene_index == 0
    assert isinstance(shot_id, str)
    assert len(shot_id) == 36  # UUID format
    assert new_video_key == f"projects/proj-123/scenes/scene-1/{shot_id}.mp4"
    assert old_video_key is None


@pytest.mark.asyncio
async def test_update_scene_record_returns_none_for_old_key_on_first_recording():
    """Test update_scene_record returns None for old_video_key on first recording."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-456",
                "groupId": "group-789",
                "projectName": "Test Project 2",
                "ownerUserId": "owner-2",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-2",
                        "scenePrincipal": "interview",
                        "videoKey": None,
                        "assignedUserIds": ["staff-001"],
                    },
                ],
            },
        ],
    )

    staff = User(
        user_id="staff-001",
        user_name="Staff",
        group_id="group-789",
        role=UserRole.STAFF,
    )

    _, _, _, _, old_video_key = await update_scene_record(
        projects_db=database,
        project_id="proj-456",
        scene_id="scene-2",
        user=staff,
    )

    assert old_video_key is None


@pytest.mark.asyncio
async def test_update_scene_record_returns_old_key_on_subsequent_recording():
    """Test update_scene_record returns old_video_key on subsequent recording."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-999",
                "groupId": "group-abc",
                "projectName": "Test Project 3",
                "ownerUserId": "owner-3",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-3",
                        "scenePrincipal": "product-shot",
                        "videoKey": "projects/proj-999/scenes/scene-3/old-shot-123.mp4",
                        "assignedUserIds": ["staff-002"],
                    },
                ],
            },
        ],
    )

    staff = User(
        user_id="staff-002",
        user_name="Staff",
        group_id="group-abc",
        role=UserRole.STAFF,
    )

    _, _, _, _, old_video_key = await update_scene_record(
        projects_db=database,
        project_id="proj-999",
        scene_id="scene-3",
        user=staff,
    )

    assert old_video_key == "projects/proj-999/scenes/scene-3/old-shot-123.mp4"


@pytest.mark.asyncio
async def test_update_scene_record_raises_404_when_project_not_found():
    """Test update_scene_record raises ClientNotFoundError when project not found."""
    database = MockDatabase(initial_items=[])

    staff = User(
        user_id="staff-123",
        user_name="Staff",
        group_id="group-456",
        role=UserRole.STAFF,
    )

    with pytest.raises(ClientNotFoundError, match="Project not found"):
        await update_scene_record(
            projects_db=database,
            project_id="nonexistent-project",
            scene_id="scene-1",
            user=staff,
        )


@pytest.mark.asyncio
async def test_update_scene_record_raises_404_when_scene_not_found():
    """Test update_scene_record raises ClientNotFoundError when scene not found."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-777",
                "groupId": "group-888",
                "projectName": "Test Project 4",
                "ownerUserId": "owner-4",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-existing",
                        "scenePrincipal": "existing-scene",
                        "assignedUserIds": ["staff-999"],
                    },
                ],
            },
        ],
    )

    staff = User(
        user_id="staff-999",
        user_name="Staff",
        group_id="group-888",
        role=UserRole.STAFF,
    )

    with pytest.raises(ClientNotFoundError, match="Scene not found"):
        await update_scene_record(
            projects_db=database,
            project_id="proj-777",
            scene_id="nonexistent-scene",
            user=staff,
        )


@pytest.mark.asyncio
async def test_update_scene_record_raises_403_when_wrong_group():
    """Test update_scene_record raises ClientAuthorizationError for wrong group."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-111",
                "groupId": "group-aaa",
                "projectName": "Test Project 5",
                "ownerUserId": "owner-5",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-1",
                        "scenePrincipal": "group-scene",
                        "assignedUserIds": ["staff-bbb"],
                    },
                ],
            },
        ],
    )

    other_staff = User(
        user_id="staff-ccc",
        user_name="Other Staff",
        group_id="group-bbb",
        role=UserRole.STAFF,
    )

    with pytest.raises(
        ClientAuthorizationError,
        match="Access to other group's project is forbidden",
    ):
        await update_scene_record(
            projects_db=database,
            project_id="proj-111",
            scene_id="scene-1",
            user=other_staff,
        )


@pytest.mark.asyncio
async def test_update_scene_record_raises_403_when_not_assigned():
    """Test update_scene_record raises ClientAuthorizationError when not assigned."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-222",
                "groupId": "group-ddd",
                "projectName": "Test Project 6",
                "ownerUserId": "owner-6",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-1",
                        "scenePrincipal": "assigned-scene",
                        "assignedUserIds": ["staff-assigned"],
                    },
                ],
            },
        ],
    )

    unassigned_staff = User(
        user_id="staff-unassigned",
        user_name="Unassigned Staff",
        group_id="group-ddd",
        role=UserRole.STAFF,
    )

    with pytest.raises(
        ClientAuthorizationError,
        match="Not assigned to this scene",
    ):
        await update_scene_record(
            projects_db=database,
            project_id="proj-222",
            scene_id="scene-1",
            user=unassigned_staff,
        )
