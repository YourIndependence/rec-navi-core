# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for create_project use case."""

import pytest

from recnavi.application.project.create_project import create_project_usecase
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_create_project_usecase_saves_to_database():
    """Test create_project_usecase saves project to database."""
    projects_db = MockDatabase()
    owner = User(
        user_id="user-owner",
        user_name="Owner User",
        role=UserRole.OWNER,
        group_id="group-123",
    )

    project = await create_project_usecase(
        projects_db=projects_db,
        project_name="Test Project",
        description="Test description",
        scene_principals=["opening", "main"],
        assigned_user_ids=["user-001"],
        owner=owner,
    )

    saved_item = await projects_db.get_item(
        key={"projectId": project.project_id},
    )
    assert saved_item is not None
    assert saved_item["projectName"] == "Test Project"
    assert saved_item["groupId"] == "group-123"
    assert saved_item["ownerUserId"] == "user-owner"
    assert len(saved_item["scenes"]) == 2


@pytest.mark.asyncio
async def test_create_project_usecase_returns_created_project():
    """Test create_project_usecase returns the created Project."""
    projects_db = MockDatabase()
    owner = User(
        user_id="user-owner",
        user_name="Owner User",
        role=UserRole.OWNER,
        group_id="group-123",
    )

    project = await create_project_usecase(
        projects_db=projects_db,
        project_name="Test Project",
        description="Test description",
        scene_principals=["opening"],
        assigned_user_ids=[],
        owner=owner,
    )

    assert isinstance(project, Project)
    assert project.project_name == "Test Project"
    assert project.group_id == "group-123"
    assert project.owner_user_id == "user-owner"
    assert project.version == 0


@pytest.mark.asyncio
async def test_create_project_usecase_propagates_authorization_error():
    """Test create_project_usecase propagates authorization errors from Core layer."""
    projects_db = MockDatabase()
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
        await create_project_usecase(
            projects_db=projects_db,
            project_name="Test Project",
            description="",
            scene_principals=["opening"],
            assigned_user_ids=[],
            owner=staff,
        )
