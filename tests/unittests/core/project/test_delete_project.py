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
from tests.mockups.mock_object_storage import MockObjectStorage


BUCKET = "test-bucket"


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

    storage = MockObjectStorage(bucket_name=BUCKET)
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
        storage=storage,
    )

    assert project_id == "proj-123"

    deleted_project = await database.get_item({"projectId": "proj-123"})
    assert deleted_project is None


@pytest.mark.asyncio
async def test_delete_project_admin_can_delete_project_in_their_group():
    """Test an admin can delete a project in their own group."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-admin",
                "groupId": "group-admin",
                "projectName": "Admin Project",
                "ownerUserId": "admin-123",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": [],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )
    admin = User(
        user_id="admin-123",
        user_name="Admin User",
        group_id="group-admin",
        role=UserRole.ADMIN,
    )

    project_id = await delete_project(
        projects_db=database,
        project_id="proj-admin",
        user=admin,
        storage=MockObjectStorage(bucket_name=BUCKET),
    )

    assert project_id == "proj-admin"
    assert await database.get_item({"projectId": "proj-admin"}) is None


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

    storage = MockObjectStorage(bucket_name=BUCKET)
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
            storage=storage,
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

    storage = MockObjectStorage(bucket_name=BUCKET)
    other_owner = User(
        user_id="owner-bbb",
        user_name="Other Owner",
        group_id="group-bbb",
        role=UserRole.OWNER,
    )

    with pytest.raises(
        ClientAuthorizationError,
        match="Only owners can delete projects",
    ):
        await delete_project(
            projects_db=database,
            project_id="proj-999",
            user=other_owner,
            storage=storage,
        )

    still_exists = await database.get_item({"projectId": "proj-999"})
    assert still_exists is not None


@pytest.mark.asyncio
async def test_delete_project_nonexistent_gets_404():
    """Test deleting nonexistent project returns 404."""
    database = MockDatabase(initial_items=[])

    storage = MockObjectStorage(bucket_name=BUCKET)
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
            storage=storage,
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

    storage = MockObjectStorage(bucket_name=BUCKET)
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
        storage=storage,
    )
    assert project_id == "proj-777"

    with pytest.raises(ClientNotFoundError, match="Project not found"):
        await delete_project(
            projects_db=database,
            project_id="proj-777",
            user=owner,
            storage=storage,
        )


@pytest.mark.asyncio
async def test_delete_project_deletes_only_project_prefix_objects():
    """Test owner deletion removes only the project's stored media."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-1",
                "groupId": "group-1",
                "projectName": "Media Project",
                "ownerUserId": "owner-1",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": [],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )
    storage = MockObjectStorage(bucket_name=BUCKET)
    storage.objects = {
        (BUCKET, "projects/proj-1/a.mp4"): (b"a", "video/mp4"),
        (BUCKET, "projects/proj-1/b.mp4"): (b"b", "video/mp4"),
        (BUCKET, "projects/proj-10/c.mp4"): (b"c", "video/mp4"),
        ("other-bucket", "projects/proj-1/d.mp4"): (b"d", "video/mp4"),
    }
    owner = User(
        user_id="owner-1",
        user_name="Owner User",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    await delete_project(
        projects_db=database,
        project_id="proj-1",
        user=owner,
        storage=storage,
    )

    assert set(storage.objects) == {
        (BUCKET, "projects/proj-10/c.mp4"),
        ("other-bucket", "projects/proj-1/d.mp4"),
    }


@pytest.mark.asyncio
async def test_delete_project_forbidden_keeps_stored_objects():
    """Test rejected deletion leaves stored media untouched."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-2",
                "groupId": "group-a",
                "projectName": "Kept Project",
                "ownerUserId": "owner-a",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": [],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )
    storage = MockObjectStorage(bucket_name=BUCKET)
    storage.objects = {(BUCKET, "projects/proj-2/a.mp4"): (b"a", "video/mp4")}
    other_owner = User(
        user_id="owner-b",
        user_name="Other Owner",
        group_id="group-b",
        role=UserRole.OWNER,
    )

    with pytest.raises(ClientAuthorizationError):
        await delete_project(
            projects_db=database,
            project_id="proj-2",
            user=other_owner,
            storage=storage,
        )

    assert (BUCKET, "projects/proj-2/a.mp4") in storage.objects
