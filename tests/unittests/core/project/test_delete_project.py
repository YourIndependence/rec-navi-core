# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for delete_project core logic."""

import pytest

from recnavi.core.project.delete_project import delete_project
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_delete_project_owner_can_delete():
    """Test owner can delete their project."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-123",
                "groupId": "group-456",
                "projectName": "Test Project",
                "ownerUserId": "owner-789",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": [],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )

    owner = User(
        user_id="owner-789",
        user_name="Owner User",
        group_id="group-456",
        role=UserRole.OWNER,
    )

    project_id = await delete_project(
        projects_db=database,
        project_id="proj-123",
        user=owner,
    )

    assert project_id == "proj-123"

    deleted_project = await database.get_item({"projectId": "proj-123"})
    assert deleted_project is None


@pytest.mark.asyncio
async def test_delete_project_staff_gets_403():
    """Test staff user gets 403 when trying to delete project."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-456",
                "groupId": "group-789",
                "projectName": "Staff Project",
                "ownerUserId": "owner-001",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": ["staff-002"],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )

    staff = User(
        user_id="staff-002",
        user_name="Staff User",
        group_id="group-789",
        role=UserRole.STAFF,
    )

    with pytest.raises(
        ClientAuthorizationError,
        match="Only owners can delete projects",
    ):
        await delete_project(
            projects_db=database,
            project_id="proj-456",
            user=staff,
        )

    still_exists = await database.get_item({"projectId": "proj-456"})
    assert still_exists is not None


@pytest.mark.asyncio
async def test_delete_project_other_group_gets_403():
    """Test user from other group gets 403."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-999",
                "groupId": "group-aaa",
                "projectName": "Private Project",
                "ownerUserId": "owner-aaa",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": [],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )

    other_owner = User(
        user_id="owner-bbb",
        user_name="Other Owner",
        group_id="group-bbb",
        role=UserRole.OWNER,
    )

    with pytest.raises(
        ClientAuthorizationError,
        match="Access to other group's project",
    ):
        await delete_project(
            projects_db=database,
            project_id="proj-999",
            user=other_owner,
        )

    still_exists = await database.get_item({"projectId": "proj-999"})
    assert still_exists is not None


@pytest.mark.asyncio
async def test_delete_project_nonexistent_gets_404():
    """Test deleting nonexistent project returns 404."""
    database = MockDatabase(initial_items=[])

    owner = User(
        user_id="owner-123",
        user_name="Owner User",
        group_id="group-456",
        role=UserRole.OWNER,
    )

    with pytest.raises(ClientNotFoundError, match="Project not found"):
        await delete_project(
            projects_db=database,
            project_id="nonexistent-project",
            user=owner,
        )


@pytest.mark.asyncio
async def test_delete_project_idempotent_second_delete_gets_404():
    """Test second deletion of same project returns 404 (idempotent at API layer)."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-777",
                "groupId": "group-ccc",
                "projectName": "Idempotent Test",
                "ownerUserId": "owner-ccc",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": [],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )

    owner = User(
        user_id="owner-ccc",
        user_name="Owner User",
        group_id="group-ccc",
        role=UserRole.OWNER,
    )

    project_id = await delete_project(
        projects_db=database,
        project_id="proj-777",
        user=owner,
    )
    assert project_id == "proj-777"

    with pytest.raises(ClientNotFoundError, match="Project not found"):
        await delete_project(
            projects_db=database,
            project_id="proj-777",
            user=owner,
        )
