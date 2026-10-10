# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_projects use case."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.get_projects import get_projects_usecase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_projects_usecase_delegates_to_core():
    """Test get_projects_usecase delegates and returns the core output."""
    projects_db = MockDatabase()
    user = User(
        user_id="owner-1",
        user_name="owner",
        role=UserRole.OWNER,
        group_id="group-123",
    )
    expected_output = object()

    with patch(
        "recnavi.application.project.get_projects.get_group_projects",
        new=AsyncMock(return_value=expected_output),
    ) as mock_get_group_projects:
        result = await get_projects_usecase(
            projects_db=projects_db,
            user=user,
            limit=20,
            cursor="cursor-1",
        )

    mock_get_group_projects.assert_awaited_with(
        projects_db=projects_db,
        user=user,
        limit=20,
        cursor="cursor-1",
    )
    assert result is expected_output
