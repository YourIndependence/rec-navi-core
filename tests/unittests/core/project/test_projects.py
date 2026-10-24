# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Project listing, pagination and monitoring contracts."""

import logging

import pytest

from recnavi.core.project.projects import build_filter_stats
from recnavi.core.project.projects import get_projects
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_metrics_publisher import MockMetricsPublisher


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
                "assignedUserIds": ["test-user-id"],
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
        user_id="test-user-id",
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
        user_id="test-user-id",
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
                "ownerUserId": "test-user-id",
                "createdAt": f"2026-09-{i:02d}T00:00:00Z",
                "updatedAt": f"2026-09-{i:02d}T00:00:00Z",
                "description": f"Description {i}",
                "status": "in_progress",
                "assignedUserIds": [],
                "scenes": [],
            }
            for i in range(1, 6)
        ],
    )
    page1_projects, page1_cursor = await get_projects(
        projects_db=mock_db,
        user_id="test-user-id",
        group_id="group-123",
        limit=2,
    )
    assert len(page1_projects) == 2
    assert page1_cursor is not None
    page2_projects, page2_cursor = await get_projects(
        projects_db=mock_db,
        user_id="test-user-id",
        group_id="group-123",
        limit=2,
        cursor=page1_cursor,
    )
    assert len(page2_projects) == 2
    assert page2_cursor is not None
    page3_projects, page3_cursor = await get_projects(
        projects_db=mock_db,
        user_id="test-user-id",
        group_id="group-123",
        limit=2,
        cursor=page2_cursor,
    )
    assert len(page3_projects) == 1
    assert page3_cursor is None


@pytest.mark.asyncio
async def test_get_projects_does_not_mix_groups():
    """Test get_projects does not return projects from other groups."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-g1-1",
                "groupId": "group-123",
                "projectName": "G1 Project 1",
                "ownerUserId": "test-user-id",
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
                "ownerUserId": "test-user-id",
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
        user_id="test-user-id",
        group_id="group-123",
    )
    assert len(projects) == 2
    assert all(p.group_id == "group-123" for p in projects)
    project_ids = {p.project_id for p in projects}
    assert project_ids == {"proj-g1-1", "proj-g1-2"}


@pytest.mark.asyncio
async def test_get_projects_filters_by_assigned_user():
    """Test get_projects returns only projects where user is assigned."""
    from recnavi.core.project.projects import get_projects

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
    projects, next_cursor = await get_projects(
        projects_db=mock_db,
        group_id="group-123",
        user_id="staff-1",
    )
    assert len(projects) == 2
    project_ids = {p.project_id for p in projects}
    assert project_ids == {"proj-assigned-1", "proj-assigned-2"}
    assert next_cursor is None


@pytest.mark.asyncio
async def test_get_projects_returns_empty_when_no_assignment():
    """Test get_projects returns empty list when all projects filtered out."""
    from recnavi.core.project.projects import get_projects

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
    projects, next_cursor = await get_projects(
        projects_db=mock_db,
        group_id="group-123",
        user_id="staff-1",
    )
    assert projects == []
    assert next_cursor is None


@pytest.mark.asyncio
async def test_get_projects_does_not_return_other_group():
    """Test get_projects excludes assigned projects from other groups."""
    from recnavi.core.project.projects import get_projects

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
    projects, _ = await get_projects(
        projects_db=mock_db,
        group_id="group-123",
        user_id="staff-1",
    )
    assert len(projects) == 1
    assert projects[0].project_id == "proj-my-group"
    assert projects[0].group_id == "group-123"


@pytest.mark.asyncio
async def test_get_projects_pagination_with_filtering():
    """Test get_projects pagination returns nextCursor even with filtering.

    Important: limit is the number of items to QUERY, not RETURN.
    nextCursor may be present even when returned items < limit.
    """
    from recnavi.core.project.projects import get_projects

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
    projects, next_cursor = await get_projects(
        projects_db=mock_db,
        group_id="group-123",
        user_id="staff-1",
        limit=2,
    )
    assert len(projects) == 1
    assert projects[0].project_id == "proj-1"
    assert next_cursor is not None


@pytest.mark.asyncio
async def test_get_projects_returns_cursor_even_when_all_filtered():
    """Test nextCursor is present even when all queried items are filtered out.

    Scenario: limit=2 queries 2 items, but both are filtered out (not assigned).
    The nextCursor should still be present because more data exists in DynamoDB.
    """
    from recnavi.core.project.projects import get_projects

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
                "assignedUserIds": ["staff-2"],
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
    projects, next_cursor = await get_projects(
        projects_db=mock_db,
        group_id="group-123",
        user_id="staff-1",
        limit=2,
    )
    assert projects == []
    assert next_cursor is not None


def _db(total: int, assigned: int) -> MockDatabase:
    """Build a group with `total` projects, `assigned` of them for staff-1."""
    return MockDatabase(
        initial_items=[
            {
                "projectId": f"proj-{i}",
                "groupId": "group-1",
                "projectName": f"Project {i}",
                "ownerUserId": "owner-1",
                "createdAt": f"2026-09-{i + 1:02d}T00:00:00Z",
                "updatedAt": f"2026-09-{i + 1:02d}T00:00:00Z",
                "description": "",
                "status": "in_progress",
                "assignedUserIds": ["staff-1" if i < assigned else "staff-2"],
                "scenes": [],
            }
            for i in range(total)
        ],
    )


@pytest.mark.parametrize(
    ("queried", "filtered", "expected_ratio"),
    [(0, 0, 0.0), (10, 10, 0.0), (10, 5, 50.0), (5, 1, 80.0), (4, 0, 100.0)],
)
def test_build_filter_stats_computes_ratio(queried, filtered, expected_ratio):
    """Test the dropped percentage is computed from queried and kept rows."""
    stats = build_filter_stats(queried_count=queried, filtered_count=filtered)
    assert stats.queried_count == queried
    assert stats.filtered_count == filtered
    assert stats.filter_ratio == expected_ratio


@pytest.mark.asyncio
@pytest.mark.parametrize(("total", "assigned"), [(5, 1), (5, 0)])
async def test_get_projects_warns_when_80_percent_or_more_dropped(
    caplog,
    total,
    assigned,
):
    """Test a WARNING with the counts is logged at or above the threshold."""
    with caplog.at_level(logging.WARNING):
        await get_projects(
            projects_db=_db(total, assigned),
            user_id="staff-1",
            group_id="group-1",
        )
    messages = [r.getMessage() for r in caplog.records if r.levelno >= 30]
    assert len(messages) == 1
    assert f"queried_count={total}" in messages[0]
    assert f"filtered_count={assigned}" in messages[0]
    assert "filter_ratio=" in messages[0]


@pytest.mark.asyncio
@pytest.mark.parametrize(("total", "assigned"), [(5, 2), (5, 5), (0, 0)])
async def test_get_projects_does_not_warn_below_threshold(
    caplog,
    total,
    assigned,
):
    """Test no WARNING is logged below the threshold or for an empty page."""
    with caplog.at_level(logging.WARNING):
        await get_projects(
            projects_db=_db(total, assigned),
            user_id="staff-1",
            group_id="group-1",
        )
    assert [r for r in caplog.records if r.levelno >= 30] == []


@pytest.mark.asyncio
async def test_get_projects_records_metrics():
    """Test the page's filter statistics are published to the metrics publisher."""
    metrics = MockMetricsPublisher()
    await get_projects(
        projects_db=_db(5, 2),
        user_id="staff-1",
        group_id="group-1",
        metrics=metrics,
    )
    assert len(metrics.published) == 1
    stats = metrics.published[0]
    assert (stats.queried_count, stats.filtered_count) == (5, 2)
    assert stats.filter_ratio == 60.0
