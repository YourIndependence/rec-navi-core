# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for Project type."""

from datetime import UTC
from datetime import datetime

import pytest

from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientNotFoundError


def test_project_type_has_version_field_with_default():
    """Test Project type has version field with default."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-789",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )

    assert hasattr(project, "version")
    assert project.version == 0


def test_project_type_accepts_custom_version():
    """Test Project type accepts custom version value."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-789",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        version=5,
    )

    assert project.version == 5


def test_project_type_has_updated_at_field():
    """Test Project type has updated_at field."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-789",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T12:00:00Z",
    )

    assert hasattr(project, "updated_at")
    assert project.updated_at == "2026-01-02T12:00:00Z"


def test_project_preserves_existing_fields():
    """Test Project type preserves all existing fields."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-789",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        description="Test description",
        assigned_user_ids=["user-001", "user-002"],
        status=ProjectStatus.SUBMITTED,
        version=3,
    )

    assert project.project_id == "proj-123"
    assert project.group_id == "group-456"
    assert project.project_name == "Test Project"
    assert project.owner_user_id == "user-789"
    assert project.description == "Test description"
    assert project.assigned_user_ids == ["user-001", "user-002"]
    assert project.status == ProjectStatus.SUBMITTED
    assert project.version == 3
    assert len(project.scenes) == 0  # default_factory=list


def test_project_update_scene_replaces_matching_scene_and_increments_version():
    """Test Project.update_scene replaces by ID and advances its version."""
    first_scene = Scene(
        scene_id="scene-1",
        scene_principal="opening",
    )
    target_scene = Scene(
        scene_id="scene-2",
        scene_principal="cooking",
    )
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-owner",
        created_at="2026-01-01T00:00:00Z",
        scenes=[first_scene, target_scene],
        version=4,
    )
    recorded_scene = Scene(
        scene_id="scene-2",
        scene_principal="cooking",
        status=SceneStatus.PENDING,
        video_key="videos/scene-2.mp4",
        thumbnail_key="thumbnails/scene-2.jpg",
        created_by="staff-1",
        created_at="2026-01-02T00:00:00Z",
    )

    before_update = datetime.now(UTC)
    result = project.update_scene(recorded_scene)
    after_update = datetime.now(UTC)

    assert project.scenes[0] == first_scene
    assert project.scenes[1] == recorded_scene
    assert project.version == 5
    assert result is None
    updated_at = datetime.fromisoformat(project.updated_at)
    assert before_update <= updated_at <= after_update


def test_project_update_scene_raises_when_scene_is_missing():
    """Test Project.update_scene raises when no scene has the given ID."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-owner",
        created_at="2026-01-01T00:00:00Z",
    )
    missing_scene = Scene(
        scene_id="scene-missing",
        scene_principal="cooking",
    )

    with pytest.raises(ClientNotFoundError, match="Scene not found"):
        project.update_scene(missing_scene)


def test_project_validate_permission_allows_owner():
    """Test Project.validate_permission() allows the project owner."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-owner",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        assigned_user_ids=[],
    )

    user = User(
        user_id="user-owner",
        user_name="Owner",
        group_id="group-456",
        role=UserRole.OWNER,
    )

    assert project.validate_permission(user=user, as_role=UserRole.OWNER)


def test_project_validate_permission_allows_assigned_staff():
    """Test Project.validate_permission() allows assigned staff."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-owner",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        assigned_user_ids=["user-staff-1", "user-staff-2"],
    )

    user = User(
        user_id="user-staff-1",
        user_name="Staff 1",
        group_id="group-456",
        role=UserRole.STAFF,
    )

    assert project.validate_permission(user=user, as_role=UserRole.STAFF)


def test_project_validate_permission_allows_admin_across_groups():
    """Test admins can access projects from any group."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-owner",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        assigned_user_ids=[],
    )

    user = User(
        user_id="user-other",
        user_name="Other User",
        group_id="group-999",
        role=UserRole.ADMIN,
    )

    assert project.validate_permission(user=user, as_role=UserRole.ADMIN)


def test_project_validate_permission_allows_owner_to_act_as_staff():
    """Test a project owner may access their project as staff."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-owner",
        created_at="2026-01-01T00:00:00Z",
        assigned_user_ids=[],
    )
    user = User(
        user_id="user-owner",
        user_name="Owner",
        group_id="group-456",
        role=UserRole.OWNER,
    )

    assert project.validate_permission(user=user, as_role=UserRole.STAFF)


def test_project_validate_permission_rejects_non_assigned_same_group():
    """Test Project.validate_permission() rejects unassigned staff."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-owner",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        assigned_user_ids=["user-staff-1"],
    )

    user = User(
        user_id="user-staff-2",
        user_name="Staff 2",
        group_id="group-456",
        role=UserRole.STAFF,
    )

    assert not project.validate_permission(user=user, as_role=UserRole.STAFF)
