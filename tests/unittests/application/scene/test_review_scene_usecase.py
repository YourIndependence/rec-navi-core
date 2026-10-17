# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for review_scene_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.review_scene_usecase import review_scene_usecase
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


@pytest.mark.asyncio
async def test_usecase_delegates_to_review_scene():
    """Test usecase delegates to core review_scene collaborator."""
    mock_db = AsyncMock()
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    expected_output = Project.model_validate(
        {
            "projectId": "proj-123",
            "groupId": "group-1",
            "ownerUserId": "owner-1",
            "projectName": "Test Project",
            "status": "in_progress",
            "createdAt": "2026-01-01T00:00:00Z",
            "scenes": [],
        },
    )
    mock_storage = AsyncMock()

    with patch(
        "recnavi.application.scene.review_scene_usecase.review_scene",
        new=AsyncMock(return_value=expected_output),
    ) as mock_review_scene:
        result = await review_scene_usecase(
            projects_db=mock_db,
            project_id="proj-123",
            scene_id="scene-456",
            result="approve",
            review_comment="Looks great!",
            user=user,
            storage=mock_storage,
        )

    mock_review_scene.assert_awaited_once_with(
        projects_db=mock_db,
        project_id="proj-123",
        scene_id="scene-456",
        result="approve",
        review_comment="Looks great!",
        user=user,
        storage=mock_storage,
    )
    assert result is expected_output
