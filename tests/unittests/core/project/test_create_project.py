# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for create_project domain logic."""

import pytest

from recnavi.core.project.create_project import create_project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from tests.mockups.mock_database import MockDatabase


@pytest.fixture
def projects_db() -> MockDatabase:
    """Provide an isolated database for each test."""
    return MockDatabase()


@pytest.mark.asyncio
async def test_create_project_returns_project_with_owner(
    projects_db: MockDatabase,
):
    """Test create_project returns Project with owner information."""
    owner = User(
        user_id="user-owner",
        user_name="Owner User",
        role=UserRole.OWNER,
        group_id="group-123",
    )

    project = await create_project(
        projects_db=projects_db,
        project_name="Test Project",
        description="Test description",
        scene_principals=["opening", "main"],
        assigned_user_ids=["user-001"],
        owner=owner,
    )

    assert project.project_id is not None
    assert project.group_id == "group-123"
    assert project.project_name == "Test Project"
    assert project.description == "Test description"
    assert project.owner_user_id == "user-owner"
    assert project.assigned_user_ids == ["user-001"]
    assert project.status == ProjectStatus.IN_PROGRESS
    assert project.created_at is not None
    assert project.updated_at is not None
    saved_item = await projects_db.get_item(
        key={"projectId": project.project_id},
    )
    assert saved_item is not None


@pytest.mark.asyncio
async def test_create_project_generates_unique_scene_ids(
    projects_db: MockDatabase,
):
    """Test create_project generates unique scene_id for each scene."""
    owner = User(
        user_id="user-owner",
        user_name="Owner User",
        role=UserRole.OWNER,
        group_id="group-123",
    )

    project = await create_project(
        projects_db=projects_db,
        project_name="Test Project",
        description="",
        scene_principals=["opening", "main", "closing"],
        assigned_user_ids=[],
        owner=owner,
    )

    assert len(project.scenes) == 3
    scene_ids = [scene.scene_id for scene in project.scenes]
    assert len(scene_ids) == len(set(scene_ids))  # All unique


@pytest.mark.asyncio
async def test_create_project_allows_duplicate_scene_principals(
    projects_db: MockDatabase,
):
    """Test create_project allows duplicate scenePrincipal values."""
    owner = User(
        user_id="user-owner",
        user_name="Owner User",
        role=UserRole.OWNER,
        group_id="group-123",
    )

    project = await create_project(
        projects_db=projects_db,
        project_name="Two Dishes",
        description="",
        scene_principals=["cooking", "cooking"],
        assigned_user_ids=[],
        owner=owner,
    )

    assert len(project.scenes) == 2
    assert project.scenes[0].scene_principal == "cooking"
    assert project.scenes[1].scene_principal == "cooking"
    assert project.scenes[0].scene_id != project.scenes[1].scene_id


@pytest.mark.asyncio
async def test_create_project_allows_empty_scenes(projects_db: MockDatabase):
    """Test create_project allows empty scene_principals list."""
    owner = User(
        user_id="user-owner",
        user_name="Owner User",
        role=UserRole.OWNER,
        group_id="group-123",
    )

    project = await create_project(
        projects_db=projects_db,
        project_name="Empty Project",
        description="",
        scene_principals=[],
        assigned_user_ids=[],
        owner=owner,
    )

    assert len(project.scenes) == 0


@pytest.mark.asyncio
async def test_create_project_sets_scene_status_to_not_recorded(
    projects_db: MockDatabase,
):
    """Test create_project sets all scenes to status NOT_RECORDED."""
    owner = User(
        user_id="user-owner",
        user_name="Owner User",
        role=UserRole.OWNER,
        group_id="group-123",
    )

    project = await create_project(
        projects_db=projects_db,
        project_name="Test Project",
        description="",
        scene_principals=["opening", "main"],
        assigned_user_ids=[],
        owner=owner,
    )

    for scene in project.scenes:
        assert scene.status == SceneStatus.NOT_RECORDED


@pytest.mark.asyncio
async def test_create_project_applies_assigned_users_to_scenes(
    projects_db: MockDatabase,
):
    """Test create_project applies assigned_user_ids to all scenes."""
    owner = User(
        user_id="user-owner",
        user_name="Owner User",
        role=UserRole.OWNER,
        group_id="group-123",
    )

    project = await create_project(
        projects_db=projects_db,
        project_name="Test Project",
        description="",
        scene_principals=["opening", "main"],
        assigned_user_ids=["user-001", "user-002"],
        owner=owner,
    )

    for scene in project.scenes:
        assert scene.assigned_user_ids == ["user-001", "user-002"]


@pytest.mark.asyncio
async def test_create_project_sets_version_to_zero(projects_db: MockDatabase):
    """Test create_project sets version to 0 for new projects."""
    owner = User(
        user_id="user-owner",
        user_name="Owner User",
        role=UserRole.OWNER,
        group_id="group-123",
    )

    project = await create_project(
        projects_db=projects_db,
        project_name="Test Project",
        description="",
        scene_principals=["opening"],
        assigned_user_ids=[],
        owner=owner,
    )

    assert project.version == 0


@pytest.mark.asyncio
async def test_create_project_raises_403_for_staff(projects_db: MockDatabase):
    """Test create_project raises 403 when called by staff."""
    staff = User(
        user_id="user-staff",
        user_name="Staff User",
        role=UserRole.STAFF,
        group_id="group-123",
    )

    with pytest.raises(
        ClientAuthorizationError,
        match="Only owners can create projects",
    ):
        await create_project(
            projects_db=projects_db,
            project_name="Test Project",
            description="",
            scene_principals=["opening"],
            assigned_user_ids=[],
            owner=staff,
        )


@pytest.mark.asyncio
async def test_create_project_raises_403_for_admin(projects_db: MockDatabase):
    """Test create_project raises 403 when called by admin."""
    admin = User(
        user_id="user-admin",
        user_name="Admin User",
        role=UserRole.ADMIN,
        group_id="group-123",
    )

    await create_project(
        projects_db=projects_db,
        project_name="Test Project",
        description="",
        scene_principals=["opening"],
        assigned_user_ids=[],
        owner=admin,
    )
