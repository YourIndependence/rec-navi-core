# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for Project type."""

from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


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


def test_project_is_accessible_returns_true_for_owner():
    """Test Project.is_accessible() returns True when user is the owner."""
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

    assert project.is_accessible(user=user) is True


def test_project_is_accessible_returns_true_for_assigned_staff():
    """Test Project.is_accessible() returns True for assigned staff."""
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

    assert project.is_accessible(user=user) is True


def test_project_is_accessible_returns_false_for_different_group():
    """Test Project.is_accessible() returns False for different group user."""
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
        role=UserRole.OWNER,
    )

    assert project.is_accessible(user=user) is False


def test_project_is_accessible_returns_false_for_non_assigned_same_group():
    """Test Project.is_accessible() returns False for same-group non-assigned user."""
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

    assert project.is_accessible(user=user) is False
