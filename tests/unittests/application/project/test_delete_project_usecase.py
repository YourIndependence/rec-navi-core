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
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_delete_project_usecase_delegates_to_delete_project():
    """Test usecase delegates to core delete_project collaborator."""
    database = MockDatabase()
    storage = MockObjectStorage()
    owner = User(
        user_id="owner-789",
        user_name="Owner User",
        group_id="group-456",
        role=UserRole.OWNER,
    )
    expected = "proj-123"

    with patch(
        "recnavi.application.project.delete_project_usecase.delete_project",
        new=AsyncMock(return_value=expected),
    ) as mock_delete:
        result = await delete_project_usecase(
            projects_db=database,
            project_id="proj-123",
            user=owner,
            storage=storage,
            media_bucket_name="test-bucket",
        )

    mock_delete.assert_awaited_once_with(
        projects_db=database,
        project_id="proj-123",
        user=owner,
        storage=storage,
        bucket_name="test-bucket",
    )
    assert result is expected
