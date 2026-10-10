# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for submit_project_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.submit_project_usecase import (
    submit_project_usecase,
)
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_usecase_delegates_to_submit_project():
    """Test usecase delegates to core submit_project collaborator."""
    mock_db = AsyncMock()
    user = User(
        user_id="staff-1",
        user_name="Staff One",
        group_id="group-1",
        role=UserRole.STAFF,
    )

    mock_project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        description="Test Description",
        assigned_user_ids=["staff-1"],
        scenes=[],
        status="in_progress",
        version=1,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    expected_missing = ["scene-1", "scene-2"]
    expected_result = (mock_project, expected_missing)

    with patch(
        "recnavi.application.project.submit_project_usecase.submit_project",
        new=AsyncMock(return_value=expected_result),
    ) as mock_submit:
        result = await submit_project_usecase(
            projects_db=mock_db,
            project_id="proj-123",
            user=user,
        )

    mock_submit.assert_awaited_once_with(
        projects_db=mock_db,
        project_id="proj-123",
        user=user,
    )
    assert result is expected_result


@pytest.mark.asyncio
async def test_usecase_updates_status_when_all_recorded():
    """Test usecase updates project status to SUBMITTED when every scene is recorded."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        assigned_user_ids=["staff-1"],
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

    updated_project, missing_scene_ids = await submit_project_usecase(
        projects_db=db,
        project_id="proj-123",
        user=user,
    )

    assert updated_project.status == ProjectStatus.SUBMITTED
    assert missing_scene_ids == []
    assert updated_project.updated_at != "2026-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_usecase_does_not_update_when_missing():
    """Test usecase does not update status when a scene is unrecorded."""
    project = Project(
        project_id="proj-456",
        group_id="group-2",
        owner_user_id="owner-2",
        project_name="Test Project 2",
        assigned_user_ids=["staff-2"],
        scenes=[
            Scene(
                scene_id="scene-3",
                scene_principal="cooking",
                status=SceneStatus.APPROVE,
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
        user_id="staff-2",
        user_name="Staff Two",
        group_id="group-2",
        role=UserRole.STAFF,
    )

    updated_project, missing_scene_ids = await submit_project_usecase(
        projects_db=db,
        project_id="proj-456",
        user=user,
    )

    assert updated_project.status == ProjectStatus.IN_PROGRESS
    assert missing_scene_ids == ["scene-4"]
    assert updated_project.updated_at == "2026-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_usecase_returns_only_unrecorded_scene_ids():
    """Test usecase reports only unrecorded scenes as missing."""
    project = Project(
        project_id="proj-789",
        group_id="group-3",
        owner_user_id="owner-3",
        project_name="Test Project 3",
        assigned_user_ids=["staff-3"],
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
                status=SceneStatus.NOT_RECORDED,
            ),
            Scene(
                scene_id="scene-7",
                scene_principal="outro",
                status=SceneStatus.REJECT,
                video_key="videos/scene-7.mp4",
            ),
            Scene(
                scene_id="scene-8",
                scene_principal="intro",
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
        group_id="group-3",
        role=UserRole.STAFF,
    )

    updated_project, missing_scene_ids = await submit_project_usecase(
        projects_db=db,
        project_id="proj-789",
        user=user,
    )

    assert updated_project.status == ProjectStatus.IN_PROGRESS
    assert set(missing_scene_ids) == {"scene-6", "scene-8"}
