# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for delete_project_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.delete_project_usecase import (
    delete_project_usecase,
)
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_delete_project_usecase_deletes_from_database_and_returns_project_id():
    """Test delete_project_usecase deletes project and returns project_id."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-123",
                "groupId": "group-456",
                "projectName": "Test Project",
                "ownerUserId": "owner-789",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "assignedUserIds": [],
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )

    owner = User(
        user_id="owner-789",
        user_name="Owner User",
        group_id="group-456",
        role=UserRole.OWNER,
    )

    with patch(
        "recnavi.application.project.delete_project_usecase.delete_objects_by_prefix",
    ) as mock_delete_s3:
        mock_delete_s3.return_value = AsyncMock(return_value=3)

        project_id = await delete_project_usecase(
            projects_db=database,
            project_id="proj-123",
            user=owner,
            video_bucket_name="test-bucket",
        )

    assert project_id == "proj-123"

    deleted_project = await database.get_item({"projectId": "proj-123"})
    assert deleted_project is None

    mock_delete_s3.assert_called_once_with(
        bucket_name="test-bucket",
        prefix="projects/proj-123/",
    )
