# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_my_projects_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.get_my_projects_usecase import (
    get_my_projects_usecase,
)
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_my_projects_usecase_delegates_to_get_my_projects():
    """Test usecase delegates to core get_my_projects collaborator."""
    database = MockDatabase()

    expected_projects = [
        Project(
            project_id="proj-1",
            group_id="group-1",
            owner_user_id="owner-1",
            project_name="Project 1",
            description="Description",
            assigned_user_ids=["user-1"],
            scenes=[],
            status=ProjectStatus.IN_PROGRESS,
            version=0,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        ),
    ]
    expected_cursor = "cursor123"

    with patch(
        "recnavi.application.project.get_my_projects_usecase.get_my_projects",
        new=AsyncMock(return_value=(expected_projects, expected_cursor)),
    ) as mock_get_my_projects:
        result_projects, result_cursor = await get_my_projects_usecase(
            projects_db=database,
            group_id="group-1",
            user_id="user-1",
            limit=20,
            cursor="prev-cursor",
        )

    mock_get_my_projects.assert_awaited_once_with(
        projects_db=database,
        group_id="group-1",
        user_id="user-1",
        limit=20,
        cursor="prev-cursor",
    )
    assert result_projects is expected_projects
    assert result_cursor is expected_cursor
