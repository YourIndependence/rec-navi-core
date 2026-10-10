# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_project use case."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.get_project import get_project_usecase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_get_project_usecase_delegates_to_core():
    """Test get_project_usecase delegates and returns the core output."""
    projects_db = MockDatabase()
    storage = MockObjectStorage()
    user = User(
        user_id="user-789",
        user_name="Test User",
        group_id="group-456",
        role=UserRole.OWNER,
    )
    expected_output = object()

    with patch(
        "recnavi.application.project.get_project.get_project_view",
        new=AsyncMock(return_value=expected_output),
    ) as mock_get_project_view:
        result = await get_project_usecase(
            projects_db=projects_db,
            storage=storage,
            bucket_name="bucket",
            project_id="proj-123",
            user=user,
        )

    mock_get_project_view.assert_awaited_with(
        projects_db=projects_db,
        storage=storage,
        bucket_name="bucket",
        project_id="proj-123",
        user=user,
    )
    assert result is expected_output
