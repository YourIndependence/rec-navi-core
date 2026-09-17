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
