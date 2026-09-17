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


def test_project_type_has_version_field_with_default():
    """Test Project type has version field with default value 1."""
    project = Project(
        project_id="proj-123",
        group_id="group-456",
        project_name="Test Project",
        owner_user_id="user-789",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )

    assert hasattr(project, "version")
    assert project.version == 1


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
