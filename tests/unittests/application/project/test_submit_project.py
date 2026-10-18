# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for submit_project_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.submit_project import submit_project_usecase
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_usecase_delegates_to_submit_project():
    """Test usecase delegates to core submit_project collaborator."""
    mock_db = AsyncMock()
    storage = MockObjectStorage(bucket_name="bucket")
    user = User(
        user_id="staff-1",
        user_name="Staff One",
        group_id="group-1",
        role=UserRole.STAFF,
    )

    mock_project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        description="Test Description",
        assigned_user_ids=["staff-1"],
        scenes=[],
        status=ProjectStatus.IN_PROGRESS,
        version=1,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    expected_missing = ["scene-1", "scene-2"]
    expected_output = (mock_project, expected_missing)

    with patch(
        "recnavi.application.project.submit_project.submit_project",
        new=AsyncMock(return_value=expected_output),
    ) as mock_submit:
        result = await submit_project_usecase(
            projects_db=mock_db,
            storage=storage,
            project_id="proj-123",
            user=user,
        )

    mock_submit.assert_awaited_once_with(
        projects_db=mock_db,
        storage=storage,
        project_id="proj-123",
        user=user,
    )
    assert result is expected_output
