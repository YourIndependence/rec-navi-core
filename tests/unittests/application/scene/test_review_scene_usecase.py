# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for review_scene_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.review_scene_usecase import review_scene_usecase
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_usecase_delegates_to_review_scene():
    """Test usecase delegates to core review_scene collaborator."""
    mock_db = AsyncMock()
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    mock_project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )

    mock_db.get_item = AsyncMock(return_value=mock_project.model_dump(by_alias=True))

    with patch(
        "recnavi.application.scene.review_scene_usecase.review_scene",
        new=AsyncMock(return_value=(mock_project, 0, SceneStatus.PENDING)),
    ) as mock_review_scene:
        result = await review_scene_usecase(
            projects_db=mock_db,
            project_id="proj-123",
            scene_id="scene-456",
            result="approve",
            review_comment="Looks great!",
            user=user,
        )

    mock_review_scene.assert_awaited_once_with(
        projects_db=mock_db,
        project_id="proj-123",
        scene_id="scene-456",
        result="approve",
        user=user,
    )
    assert isinstance(result, Project)
    assert result.project_id == "proj-123"


@pytest.mark.asyncio
async def test_usecase_updates_scene_status_and_metadata():
    """Test usecase updates scene status and reviewer metadata."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    updated_project = await review_scene_usecase(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result="approve",
        review_comment="Looks great!",
        user=user,
    )

    assert updated_project.scenes[0].status == SceneStatus.APPROVE
    assert updated_project.scenes[0].reviewed_by == "owner-1"
    assert updated_project.scenes[0].reviewed_at is not None
    assert updated_project.scenes[0].review_comment == "Looks great!"


@pytest.mark.asyncio
async def test_usecase_updates_project_status_on_reject():
    """Test usecase transitions SUBMITTED project to IN_PROGRESS on reject."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        status=ProjectStatus.SUBMITTED,
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.APPROVE,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    updated_project = await review_scene_usecase(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result="reject",
        review_comment="Please re-record",
        user=user,
    )

    assert updated_project.scenes[0].status == SceneStatus.REJECT
    assert updated_project.status == ProjectStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_usecase_preserves_video_keys():
    """Test usecase preserves video and thumbnail keys."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
                video_key="projects/proj-123/scenes/scene-456/shot-789.mp4",
                thumbnail_key="projects/proj-123/scenes/scene-456/shot-789_thumb.jpg",
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    updated_project = await review_scene_usecase(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result="reject",
        review_comment=None,
        user=user,
    )

    assert (
        updated_project.scenes[0].video_key
        == "projects/proj-123/scenes/scene-456/shot-789.mp4"
    )
    assert (
        updated_project.scenes[0].thumbnail_key
        == "projects/proj-123/scenes/scene-456/shot-789_thumb.jpg"
    )


@pytest.mark.asyncio
async def test_usecase_does_not_update_project_status_on_approve():
    """Test usecase does not change project status on approve."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        status=ProjectStatus.SUBMITTED,
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    updated_project = await review_scene_usecase(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result="approve",
        review_comment=None,
        user=user,
    )

    assert updated_project.status == ProjectStatus.SUBMITTED
