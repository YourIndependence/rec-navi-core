# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for review_scene core function."""

import pytest

from recnavi.core.scene.review_scene import review_scene
from recnavi.core.types.project import Project
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_review_scene_approve_returns_correct_data():
    """Test review_scene updates project with APPROVE status."""
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

    result_project = await review_scene(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result="approve",
        review_comment=None,
        user=user,
    )

    assert result_project.project_id == "proj-123"
    assert result_project.scenes[0].status == SceneStatus.APPROVE
    assert result_project.scenes[0].reviewed_by == "owner-1"
    assert result_project.scenes[0].reviewed_at is not None


@pytest.mark.asyncio
async def test_review_scene_reject_returns_correct_data():
    """Test review_scene updates project with REJECT status."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
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

    result_project = await review_scene(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result="reject",
        review_comment=None,
        user=user,
    )

    assert result_project.project_id == "proj-123"
    assert result_project.scenes[0].status == SceneStatus.REJECT
    assert result_project.scenes[0].reviewed_by == "owner-1"
    assert result_project.scenes[0].reviewed_at is not None


@pytest.mark.asyncio
async def test_review_scene_raises_403_for_non_owner():
    """Test review_scene raises 403 for non-owner user."""
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
    staff_user = User(
        user_id="staff-1",
        user_name="Test Staff",
        group_id="group-1",
        role=UserRole.STAFF,
    )

    with pytest.raises(ClientAuthorizationError):
        await review_scene(
            projects_db=db,
            project_id="proj-123",
            scene_id="scene-456",
            result="approve",
            review_comment=None,
            user=staff_user,
        )


@pytest.mark.asyncio
async def test_review_scene_raises_403_for_wrong_group():
    """Test review_scene raises 403 for different group."""
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
    other_owner = User(
        user_id="owner-2",
        user_name="Other Owner",
        group_id="group-2",
        role=UserRole.OWNER,
    )

    with pytest.raises(ClientAuthorizationError):
        await review_scene(
            projects_db=db,
            project_id="proj-123",
            scene_id="scene-456",
            result="approve",
            review_comment=None,
            user=other_owner,
        )


@pytest.mark.asyncio
async def test_review_scene_raises_404_when_scene_not_found():
    """Test review_scene raises 404 when scene not found."""
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

    with pytest.raises(ClientNotFoundError):
        await review_scene(
            projects_db=db,
            project_id="proj-123",
            scene_id="nonexistent-scene",
            result="approve",
            review_comment=None,
            user=user,
        )


@pytest.mark.asyncio
async def test_review_scene_raises_422_for_invalid_result():
    """Test review_scene raises 422 for invalid result value."""
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

    with pytest.raises(ClientUnprocessableEntityError):
        await review_scene(
            projects_db=db,
            project_id="proj-123",
            scene_id="scene-456",
            result="pending",
            review_comment=None,
            user=user,
        )


@pytest.mark.asyncio
async def test_review_scene_allows_re_review():
    """Test review_scene allows changing APPROVE to REJECT."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
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

    result_project = await review_scene(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result="reject",
        review_comment=None,
        user=user,
    )

    assert result_project.scenes[0].status == SceneStatus.REJECT
    assert result_project.scenes[0].scene_id == "scene-456"
