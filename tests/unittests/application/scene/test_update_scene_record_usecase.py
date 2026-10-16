# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for update_scene_record_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.update_scene_record_usecase import (
    update_scene_record_usecase,
)
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


@pytest.mark.asyncio
async def test_usecase_delegates_to_update_scene_record():
    """Test usecase delegates to core and returns its output unchanged."""
    projects_db = AsyncMock()
    storage = AsyncMock()
    staff = User(
        user_id="staff-789",
        user_name="Staff",
        group_id="group-456",
        role=UserRole.STAFF,
    )
    expected_output = object()

    with patch(
        "recnavi.application.scene.update_scene_record_usecase.update_scene_record",
        new=AsyncMock(return_value=expected_output),
    ) as mock_update:
        result = await update_scene_record_usecase(
            projects_db=projects_db,
            storage=storage,
            project_id="proj-123",
            scene_id="scene-1",
            video_base64="dmlkZW8=",
            thumbnail_base64="dGh1bWI=",
            user=staff,
        )

    mock_update.assert_awaited_once_with(
        projects_db=projects_db,
        storage=storage,
        project_id="proj-123",
        scene_id="scene-1",
        video_base64="dmlkZW8=",
        thumbnail_base64="dGh1bWI=",
        user=staff,
    )
    assert result is expected_output
