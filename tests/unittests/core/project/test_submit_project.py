# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for submit_project core function."""

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
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_submit_project_all_recorded():
    """Test submit_project updates status to SUBMITTED when every scene is recorded."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        assigned_user_ids=["staff-1", "staff-2"],
        scenes=[
            Scene(
                scene_id="scene-1",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
                video_key="videos/scene-1.mp4",
            ),
            Scene(
                scene_id="scene-2",
                scene_principal="interview",
                status=SceneStatus.REJECT,
                video_key="videos/scene-2.mp4",
            ),
            Scene(
                scene_id="scene-2b",
                scene_principal="outro",
                status=SceneStatus.APPROVE,
                video_key="videos/scene-2b.mp4",
            ),
        ],
        status=ProjectStatus.IN_PROGRESS,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="staff-1",
        user_name="Staff One",
        group_id="group-1",
        role=UserRole.STAFF,
    )

    result_project, missing_scene_ids = await submit_project(
        projects_db=db,
        project_id="proj-123",
        user=user,
    )

    assert result_project.project_id == "proj-123"
    assert missing_scene_ids == []
    assert result_project.status == ProjectStatus.SUBMITTED
    assert result_project.updated_at != "2026-01-01T00:00:00Z"
    stored = await db.get_item(key={"projectId": "proj-123"})
    assert stored["status"] == ProjectStatus.SUBMITTED.value


@pytest.mark.asyncio
async def test_submit_project_one_not_recorded():
    """Test submit_project returns missing scene ID and does not update status."""
    project = Project(
        project_id="proj-456",
        group_id="group-2",
        owner_user_id="owner-2",
        project_name="Test Project 2",
        assigned_user_ids=["staff-3"],
        scenes=[
            Scene(
                scene_id="scene-3",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
                video_key="videos/scene-3.mp4",
            ),
            Scene(
                scene_id="scene-4",
                scene_principal="interview",
                status=SceneStatus.NOT_RECORDED,
            ),
        ],
        status=ProjectStatus.IN_PROGRESS,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="staff-3",
        user_name="Staff Three",
        group_id="group-2",
        role=UserRole.STAFF,
    )

    result_project, missing_scene_ids = await submit_project(
        projects_db=db,
        project_id="proj-456",
        user=user,
    )

    assert result_project.project_id == "proj-456"
    assert missing_scene_ids == ["scene-4"]
    assert result_project.status == ProjectStatus.IN_PROGRESS
    assert result_project.updated_at == "2026-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_submit_project_rejected_counts_as_recorded():
    """Test rejected scene is recorded, so project is submitted."""
    project = Project(
        project_id="proj-789",
        group_id="group-3",
        owner_user_id="owner-3",
        project_name="Test Project 3",
        assigned_user_ids=["staff-4"],
        scenes=[
            Scene(
                scene_id="scene-5",
                scene_principal="cooking",
                status=SceneStatus.APPROVE,
                video_key="videos/scene-5.mp4",
            ),
            Scene(
                scene_id="scene-6",
                scene_principal="interview",
                status=SceneStatus.REJECT,
                video_key="videos/scene-6.mp4",
            ),
        ],
        status=ProjectStatus.IN_PROGRESS,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="staff-4",
        user_name="Staff Four",
        group_id="group-3",
        role=UserRole.STAFF,
    )

    result_project, missing_scene_ids = await submit_project(
        projects_db=db,
        project_id="proj-789",
        user=user,
    )

    assert result_project.project_id == "proj-789"
    assert missing_scene_ids == []
    assert result_project.status == ProjectStatus.SUBMITTED
    assert result_project.updated_at != "2026-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_submit_project_missing_video_key_is_unrecorded():
    """Test scene without a video is reported missing despite its status."""
    project = Project(
        project_id="proj-novideo",
        group_id="group-7",
        owner_user_id="owner-7",
        project_name="No Video Project",
        assigned_user_ids=["staff-9"],
        scenes=[
            Scene(
                scene_id="scene-9",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
            ),
        ],
        status=ProjectStatus.IN_PROGRESS,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="staff-9",
        user_name="Staff Nine",
        group_id="group-7",
        role=UserRole.STAFF,
    )

    result_project, missing_scene_ids = await submit_project(
        projects_db=db,
        project_id="proj-novideo",
        user=user,
    )

    assert missing_scene_ids == ["scene-9"]
    assert result_project.status == ProjectStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_submit_project_empty_scenes_raises_422():
    """Test submit_project raises 422 when project has no scenes."""
    project = Project(
        project_id="proj-empty",
        group_id="group-4",
        owner_user_id="owner-4",
        project_name="Empty Project",
        assigned_user_ids=["staff-5"],
        scenes=[],
        status=ProjectStatus.IN_PROGRESS,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="staff-5",
        user_name="Staff Five",
        group_id="group-4",
        role=UserRole.STAFF,
    )

    with pytest.raises(ClientUnprocessableEntityError):
        await submit_project(
            projects_db=db,
            project_id="proj-empty",
            user=user,
        )


@pytest.mark.asyncio
async def test_submit_project_already_submitted_raises_409():
    """Test submit_project raises 409 when project already submitted."""
    project = Project(
        project_id="proj-submitted",
        group_id="group-5",
        owner_user_id="owner-5",
        project_name="Submitted Project",
        assigned_user_ids=["staff-6"],
        scenes=[
            Scene(
                scene_id="scene-7",
                scene_principal="cooking",
                status=SceneStatus.APPROVE,
                video_key="videos/scene-7.mp4",
            ),
        ],
        status=ProjectStatus.SUBMITTED,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="staff-6",
        user_name="Staff Six",
        group_id="group-5",
        role=UserRole.STAFF,
    )

    with pytest.raises(ClientConflictError):
        await submit_project(
            projects_db=db,
            project_id="proj-submitted",
            user=user,
        )


@pytest.mark.asyncio
async def test_submit_project_not_assigned_raises_403():
    """Test submit_project raises 403 when user not in assigned_user_ids."""
    project = Project(
        project_id="proj-999",
        group_id="group-6",
        owner_user_id="owner-6",
        project_name="Test Project 6",
        assigned_user_ids=["staff-7"],
        scenes=[
            Scene(
                scene_id="scene-8",
                scene_principal="cooking",
                status=SceneStatus.APPROVE,
                video_key="videos/scene-8.mp4",
            ),
        ],
        status=ProjectStatus.IN_PROGRESS,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    unassigned_user = User(
        user_id="staff-8",
        user_name="Staff Eight",
        group_id="group-6",
        role=UserRole.STAFF,
    )

    with pytest.raises(ClientAuthorizationError):
        await submit_project(
            projects_db=db,
            project_id="proj-999",
            user=unassigned_user,
        )
