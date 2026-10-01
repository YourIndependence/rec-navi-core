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
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_my_projects_usecase_delegates_to_core():
    """Test get_my_projects_usecase delegates to get_my_projects."""
    projects_db = MockDatabase()
    user = User(
        user_id="user-123",
        user_name="Test User",
        group_id="group-456",
        role=UserRole.STAFF,
    )
    expected_output = object()

    with patch(
        "recnavi.application.project.get_my_projects_usecase.get_my_projects",
        new=AsyncMock(return_value=expected_output),
    ) as mock_get_my_projects:
        result = await get_my_projects_usecase(
            projects_db=projects_db,
            user=user,
            limit=20,
            cursor="cursor-1",
        )

    mock_get_my_projects.assert_awaited_with(
        projects_db=projects_db,
        user=user,
        limit=20,
        cursor="cursor-1",
    )
    assert result is expected_output
