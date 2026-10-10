# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for download project use case."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.download_project_usecase import (
    download_project_usecase,
)
from recnavi.core.types.project_archive import ProjectArchive
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_download_project_usecase_delegates_to_create_project_archive():
    """Test usecase delegates to core create_project_archive collaborator."""
    user = User(
        user_id="owner-1",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group-1",
    )
    project = object()
    storage = MockObjectStorage()
    expected_output = ProjectArchive(
        download_url="mock://test-bucket/archives/proj.zip?expires=3600",
        expires_in_seconds=3600,
    )

    with patch(
        "recnavi.application.project.download_project_usecase.create_project_archive",
        new=AsyncMock(return_value=expected_output),
    ) as mock_create:
        result = await download_project_usecase(
            user=user,
            project=project,
            bucket_name="test-bucket",
            storage=storage,
        )

    mock_create.assert_awaited_once_with(
        user=user,
        project=project,
        bucket_name="test-bucket",
        storage=storage,
    )
    assert result is expected_output
