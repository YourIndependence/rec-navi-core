# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for project core logic."""

import pytest

from recnavi.core.project.project import get_project
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientResourcesNotFoundError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_project_returns_project_for_owner():
    """Test get_project returns project when user is owner."""
    projects_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-123",
                "groupId": "group-456",
                "projectName": "Test Project",
                "ownerUserId": "user-789",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": [],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )

    user = User(
        user_id="user-789",
        user_name="Test Owner",
        group_id="group-456",
        role=UserRole.OWNER,
    )

    project = await get_project(
        projects_db=projects_db,
        project_id="proj-123",
        user=user,
    )

    assert project.project_id == "proj-123"
    assert project.group_id == "group-456"
    assert project.owner_user_id == "user-789"


@pytest.mark.asyncio
async def test_get_project_returns_project_for_assigned_staff():
    """Test get_project returns project for assigned staff."""
    projects_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-456",
                "groupId": "group-789",
                "projectName": "Another Project",
                "ownerUserId": "user-001",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": ["user-002", "user-003"],
                "status": "submitted",
                "version": 2,
                "scenes": [],
            },
        ],
    )

    user = User(
        user_id="user-002",
        user_name="Test Staff",
        group_id="group-789",
        role=UserRole.STAFF,
    )

    project = await get_project(
        projects_db=projects_db,
        project_id="proj-456",
        user=user,
    )

    assert project.project_id == "proj-456"
    assert project.owner_user_id == "user-001"
    assert "user-002" in project.assigned_user_ids


@pytest.mark.asyncio
async def test_get_project_raises_404_for_missing_project():
    """Test get_project raises 404 when project does not exist."""
    projects_db = MockDatabase(initial_items=[])

    user = User(
        user_id="user-123",
        user_name="Test User",
        group_id="group-456",
        role=UserRole.OWNER,
    )

    with pytest.raises(
        ClientResourcesNotFoundError,
        match="Project not found",
    ):
        await get_project(
            projects_db=projects_db,
            project_id="nonexistent-project",
            user=user,
        )


@pytest.mark.asyncio
async def test_get_project_raises_403_for_other_group():
    """Test get_project raises 403 for other group's project."""
    projects_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-999",
                "groupId": "group-aaa",
                "projectName": "Private Project",
                "ownerUserId": "user-aaa",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": [],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )

    user = User(
        user_id="user-bbb",
        user_name="User BBB",
        group_id="group-bbb",
        role=UserRole.OWNER,
    )

    with pytest.raises(
        ClientAuthorizationError,
        match="User does not have access",
    ):
        await get_project(
            projects_db=projects_db,
            project_id="proj-999",
            user=user,
        )


@pytest.mark.asyncio
async def test_get_project_raises_403_for_non_assigned_user():
    """Test get_project raises 403 for non-assigned same-group user."""
    projects_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-777",
                "groupId": "group-ccc",
                "projectName": "Team Project",
                "ownerUserId": "user-owner",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": ["user-staff-1", "user-staff-2"],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )

    user = User(
        user_id="user-staff-3",
        user_name="Staff 3",
        group_id="group-ccc",
        role=UserRole.STAFF,
    )

    with pytest.raises(
        ClientAuthorizationError,
        match="User does not have access",
    ):
        await get_project(
            projects_db=projects_db,
            project_id="proj-777",
            user=user,
        )
