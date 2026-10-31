# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for submit_project_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.submit_project import submit_project_usecase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_notifier import MockNotifier


@pytest.mark.asyncio
async def test_submit_project_usecase_delegates_to_submit_project():
    """Test usecase delegates to core submit_project collaborator."""
    projects_db = MockDatabase()
    users_db = MockDatabase()
    notifier = MockNotifier()
    staff = User(
        user_id="staff-1",
        user_name="Staff One",
        group_id="group-1",
        role=UserRole.STAFF,
    )
    expected = object()

    with patch(
        "recnavi.application.project.submit_project.submit_project",
        new=AsyncMock(return_value=expected),
    ) as mock_submit:
        result = await submit_project_usecase(
            projects_db=projects_db,
            users_db=users_db,
            notifier=notifier,
            base_url="https://example.com",
            project_id="proj-123",
            user=staff,
        )

    mock_submit.assert_awaited_once_with(
        projects_db=projects_db,
        users_db=users_db,
        notifier=notifier,
        base_url="https://example.com",
        project_id="proj-123",
        user=staff,
    )
    assert result is expected
