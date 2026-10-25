# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_my_projects use case."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.get_my_projects import get_my_projects_usecase
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_my_projects_usecase_delegates_to_core():
    """Test get_my_projects_usecase delegates and returns the core output."""
    projects_db = MockDatabase()
    expected_output = object()

    with patch(
        "recnavi.application.project.get_my_projects.get_my_projects",
        new=AsyncMock(return_value=expected_output),
    ) as mock_get_my_projects:
        result = await get_my_projects_usecase(
            projects_db=projects_db,
            user_id="staff-1",
            group_id="group-123",
            limit=20,
            cursor="cursor-1",
        )

    mock_get_my_projects.assert_awaited_with(
        projects_db=projects_db,
        user_id="staff-1",
        group_id="group-123",
        limit=20,
        cursor="cursor-1",
    )
    assert result is expected_output
