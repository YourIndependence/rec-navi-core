# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_my_projects_usecase."""

import pytest

from recnavi.application.project.get_my_projects_usecase import (
    get_my_projects_usecase,
)
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_my_projects_usecase_calls_core_correctly():
    """Test get_my_projects_usecase passes correct args to core layer."""
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
        ],
    )

    projects, next_cursor = await get_my_projects_usecase(
        projects_db=mock_db,
        group_id="group-123",
        user_id="staff-1",
        limit=20,
        cursor=None,
    )

    assert len(projects) == 1
    assert projects[0].project_id == "proj-1"
    assert next_cursor is None
