# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for create_project use case."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.create_project import create_project_usecase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_create_project_usecase_delegates_to_core():
    """Test create_project_usecase delegates and returns the core output."""
    projects_db = MockDatabase()
    owner = User(
        user_id="user-owner",
        user_name="Owner User",
        role=UserRole.OWNER,
        group_id="group-123",
    )
    expected_output = object()

    with patch(
        "recnavi.application.project.create_project.create_project",
        new=AsyncMock(return_value=expected_output),
    ) as mock_create_project:
        result = await create_project_usecase(
            projects_db=projects_db,
            project_name="Test Project",
            description="Test description",
            scene_principals=["opening", "main"],
            assigned_user_ids=["user-001"],
            owner=owner,
        )

    mock_create_project.assert_awaited_with(
        projects_db=projects_db,
        project_name="Test Project",
        description="Test description",
        scene_principals=["opening", "main"],
        assigned_user_ids=["user-001"],
        owner=owner,
    )
    assert result is expected_output
