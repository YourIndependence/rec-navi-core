# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for projects core logic."""

import pytest

from recnavi.core.project.projects import decode_cursor
from recnavi.core.project.projects import encode_cursor
from recnavi.core.project.projects import get_projects
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_encode_decode_cursor_roundtrip():
    """Test cursor encoding and decoding roundtrip."""
    original = {"groupId": "group-123", "createdAt": "2026-09-01T00:00:00Z"}

    encoded = encode_cursor(original)
    decoded = decode_cursor(encoded)

    assert decoded == original


@pytest.mark.asyncio
async def test_encode_cursor_returns_none_for_none():
    """Test encode_cursor returns None when input is None."""
    assert encode_cursor(None) is None


@pytest.mark.asyncio
async def test_decode_cursor_returns_none_for_none():
    """Test decode_cursor returns None when input is None."""
    assert decode_cursor(None) is None


@pytest.mark.asyncio
async def test_get_projects_returns_projects_for_group():
    """Test get_projects returns only projects for the specified group."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-1",
                "groupId": "group-123",
                "projectName": "Project 1",
                "ownerUserId": "user-1",
                "createdAt": "2026-09-01T00:00:00Z",
                "updatedAt": "2026-09-01T00:00:00Z",
                "description": "Description 1",
                "status": "in_progress",
                "assignedUserIds": [],
                "scenes": [],
            },
            {
                "projectId": "proj-2",
                "groupId": "group-456",
                "projectName": "Project 2",
                "ownerUserId": "user-2",
                "createdAt": "2026-09-02T00:00:00Z",
                "updatedAt": "2026-09-02T00:00:00Z",
                "description": "Description 2",
                "status": "submitted",
                "assignedUserIds": [],
                "scenes": [],
            },
        ],
    )

    projects, next_cursor = await get_projects(
        projects_db=mock_db,
        group_id="group-123",
    )

    assert len(projects) == 1
    assert projects[0].project_id == "proj-1"
    assert projects[0].group_id == "group-123"
    assert next_cursor is None


@pytest.mark.asyncio
async def test_get_projects_returns_empty_list_for_empty_group():
    """Test get_projects returns empty list when no projects exist."""
    mock_db = MockDatabase(initial_items=[])

    projects, next_cursor = await get_projects(
        projects_db=mock_db,
        group_id="group-empty",
    )

    assert projects == []
    assert next_cursor is None


@pytest.mark.asyncio
async def test_get_projects_paginates_correctly():
    """Test get_projects handles pagination across multiple pages."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "projectId": f"proj-{i}",
                "groupId": "group-123",
                "projectName": f"Project {i}",
                "ownerUserId": "user-1",
                "createdAt": f"2026-09-{i:02d}T00:00:00Z",
                "updatedAt": f"2026-09-{i:02d}T00:00:00Z",
                "description": f"Description {i}",
                "status": "in_progress",
                "assignedUserIds": [],
                "scenes": [],
            }
            for i in range(1, 6)  # 5 projects
        ],
    )

    # Page 1: limit=2
    page1_projects, page1_cursor = await get_projects(
        projects_db=mock_db,
        group_id="group-123",
        limit=2,
    )

    assert len(page1_projects) == 2
    assert page1_cursor is not None

    # Page 2: use cursor
    page2_projects, page2_cursor = await get_projects(
        projects_db=mock_db,
        group_id="group-123",
        limit=2,
        cursor=page1_cursor,
    )

    assert len(page2_projects) == 2
    assert page2_cursor is not None

    # Page 3: last page
    page3_projects, page3_cursor = await get_projects(
        projects_db=mock_db,
        group_id="group-123",
        limit=2,
        cursor=page2_cursor,
    )

    assert len(page3_projects) == 1  # Only 1 item left
    assert page3_cursor is None  # No more pages


@pytest.mark.asyncio
async def test_get_projects_does_not_mix_groups():
    """Test get_projects does not return projects from other groups."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-g1-1",
                "groupId": "group-123",
                "projectName": "G1 Project 1",
                "ownerUserId": "user-1",
                "createdAt": "2026-09-01T00:00:00Z",
                "updatedAt": "2026-09-01T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": [],
                "scenes": [],
            },
            {
                "projectId": "proj-g2-1",
                "groupId": "group-456",
                "projectName": "G2 Project 1",
                "ownerUserId": "user-2",
                "createdAt": "2026-09-02T00:00:00Z",
                "updatedAt": "2026-09-02T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": [],
                "scenes": [],
            },
            {
                "projectId": "proj-g1-2",
                "groupId": "group-123",
                "projectName": "G1 Project 2",
                "ownerUserId": "user-1",
                "createdAt": "2026-09-03T00:00:00Z",
                "updatedAt": "2026-09-03T00:00:00Z",
                "description": "",
                "status": "submitted",
                "assignedUserIds": [],
                "scenes": [],
            },
        ],
    )

    projects, _ = await get_projects(
        projects_db=mock_db,
        group_id="group-123",
    )

    assert len(projects) == 2
    assert all(p.group_id == "group-123" for p in projects)
    project_ids = {p.project_id for p in projects}
    assert project_ids == {"proj-g1-1", "proj-g1-2"}


@pytest.mark.asyncio
async def test_get_my_projects_filters_by_assigned_user():
    """Test get_my_projects returns only projects where user is assigned."""
    from recnavi.core.project.projects import get_my_projects

    mock_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-assigned-1",
                "groupId": "group-123",
                "projectName": "Assigned Project 1",
                "ownerUserId": "owner-1",
                "createdAt": "2026-09-01T00:00:00Z",
                "updatedAt": "2026-09-01T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": ["staff-1", "staff-2"],
                "scenes": [],
            },
            {
                "projectId": "proj-not-assigned",
                "groupId": "group-123",
                "projectName": "Not Assigned Project",
                "ownerUserId": "owner-1",
                "createdAt": "2026-09-02T00:00:00Z",
                "updatedAt": "2026-09-02T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": ["staff-2"],
                "scenes": [],
            },
            {
                "projectId": "proj-assigned-2",
                "groupId": "group-123",
                "projectName": "Assigned Project 2",
                "ownerUserId": "owner-1",
                "createdAt": "2026-09-03T00:00:00Z",
                "updatedAt": "2026-09-03T00:00:00Z",
                "description": "",
                "status": "submitted",
                "assignedUserIds": ["staff-1"],
                "scenes": [],
            },
        ],
    )

    projects, next_cursor = await get_my_projects(
        projects_db=mock_db,
        group_id="group-123",
        user_id="staff-1",
    )

    assert len(projects) == 2
    project_ids = {p.project_id for p in projects}
    assert project_ids == {"proj-assigned-1", "proj-assigned-2"}
    assert next_cursor is None


@pytest.mark.asyncio
async def test_get_my_projects_returns_empty_when_no_assignment():
    """Test get_my_projects returns empty list when all projects filtered out."""
    from recnavi.core.project.projects import get_my_projects

    mock_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-1",
                "groupId": "group-123",
                "projectName": "Project 1",
                "ownerUserId": "owner-1",
                "createdAt": "2026-09-01T00:00:00Z",
                "updatedAt": "2026-09-01T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": ["staff-2", "staff-3"],
                "scenes": [],
            },
            {
                "projectId": "proj-2",
                "groupId": "group-123",
                "projectName": "Project 2",
                "ownerUserId": "owner-1",
                "createdAt": "2026-09-02T00:00:00Z",
                "updatedAt": "2026-09-02T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": [],
                "scenes": [],
            },
        ],
    )

    projects, next_cursor = await get_my_projects(
        projects_db=mock_db,
        group_id="group-123",
        user_id="staff-1",
    )

    assert projects == []
    assert next_cursor is None


@pytest.mark.asyncio
async def test_get_my_projects_does_not_return_other_group():
    """Test get_my_projects excludes assigned projects from other groups."""
    from recnavi.core.project.projects import get_my_projects

    mock_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-my-group",
                "groupId": "group-123",
                "projectName": "My Group Project",
                "ownerUserId": "owner-1",
                "createdAt": "2026-09-01T00:00:00Z",
                "updatedAt": "2026-09-01T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": ["staff-1"],
                "scenes": [],
            },
            {
                "projectId": "proj-other-group",
                "groupId": "group-456",
                "projectName": "Other Group Project",
                "ownerUserId": "owner-2",
                "createdAt": "2026-09-02T00:00:00Z",
                "updatedAt": "2026-09-02T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": ["staff-1"],
                "scenes": [],
            },
        ],
    )

    projects, _ = await get_my_projects(
        projects_db=mock_db,
        group_id="group-123",
        user_id="staff-1",
    )

    assert len(projects) == 1
    assert projects[0].project_id == "proj-my-group"
    assert projects[0].group_id == "group-123"


@pytest.mark.asyncio
async def test_get_my_projects_pagination_with_filtering():
    """Test get_my_projects pagination returns nextCursor even with filtering.

    Important: limit is the number of items to QUERY, not RETURN.
    nextCursor may be present even when returned items < limit.
    """
    from recnavi.core.project.projects import get_my_projects

    mock_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-1",
                "groupId": "group-123",
                "projectName": "Project 1",
                "ownerUserId": "owner-1",
                "createdAt": "2026-09-01T00:00:00Z",
                "updatedAt": "2026-09-01T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": ["staff-1"],
                "scenes": [],
            },
            {
                "projectId": "proj-2",
                "groupId": "group-123",
                "projectName": "Project 2",
                "ownerUserId": "owner-1",
                "createdAt": "2026-09-02T00:00:00Z",
                "updatedAt": "2026-09-02T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": ["staff-2"],
                "scenes": [],
            },
            {
                "projectId": "proj-3",
                "groupId": "group-123",
                "projectName": "Project 3",
                "ownerUserId": "owner-1",
                "createdAt": "2026-09-03T00:00:00Z",
                "updatedAt": "2026-09-03T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": ["staff-1"],
                "scenes": [],
            },
        ],
    )

    projects, next_cursor = await get_my_projects(
        projects_db=mock_db,
        group_id="group-123",
        user_id="staff-1",
        limit=2,
    )

    assert len(projects) == 1
    assert projects[0].project_id == "proj-1"
    assert next_cursor is not None
