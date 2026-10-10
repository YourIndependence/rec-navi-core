# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for getMyProjects filter monitoring in get_projects."""

import logging

import pytest

from recnavi.core.project.projects import build_filter_stats
from recnavi.core.project.projects import get_projects
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_metrics_publisher import MockMetricsPublisher


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
