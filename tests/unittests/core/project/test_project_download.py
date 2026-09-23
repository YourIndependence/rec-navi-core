# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for project download validation logic."""

import pytest

from recnavi.core.project.project_download import validate_project_for_download
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


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
