# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_project use case."""

import pytest

from recnavi.application.project.get_project import get_project_use_case
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_project_use_case_returns_project():
    """Test get_project_use_case returns Project."""
    projects_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-123",
                "groupId": "group-456",
                "projectName": "Test Project",
                "description": "Test description",
                "ownerUserId": "user-789",
                "assignedUserIds": [],
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-02T00:00:00Z",
                "status": "in_progress",
                "version": 1,
                "scenes": [
                    {
                        "sceneId": "scene-001",
                        "scenePrincipal": "opening",
                        "status": "approve",
                        "videoKey": "videos/scene-001.mp4",
                        "thumbnailKey": "thumbnails/scene-001.jpg",
                        "createdBy": "user-789",
                        "createdAt": "2026-01-01T10:00:00Z",
                        "assignedAt": "2026-01-01T09:00:00Z",
                        "assignedUserIds": ["user-789"],
                    },
                ],
            },
        ],
    )

    user = User(
        user_id="user-789",
        user_name="Test User",
        group_id="group-456",
        role=UserRole.OWNER,
    )

    project = await get_project_use_case(
        projects_db=projects_db,
        project_id="proj-123",
        user=user,
    )

    assert isinstance(project, Project)
    assert project.project_id == "proj-123"
    assert project.group_id == "group-456"
    assert project.version == 1
    assert len(project.scenes) == 1
    assert project.scenes[0].scene_id == "scene-001"
    assert project.scenes[0].video_key == "videos/scene-001.mp4"
    assert project.scenes[0].thumbnail_key == "thumbnails/scene-001.jpg"


@pytest.mark.asyncio
async def test_get_project_use_case_propagates_authorization_error():
    """Test get_project_use_case propagates authorization errors from Core layer."""
    projects_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-999",
                "groupId": "group-aaa",
                "projectName": "Private Project",
                "description": "",
                "ownerUserId": "user-aaa",
                "assignedUserIds": [],
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "status": "in_progress",
                "version": 1,
                "scenes": [],
            },
        ],
    )

    user = User(
        user_id="user-bbb",
        user_name="User BBB",
        group_id="group-bbb",
        role=UserRole.OWNER,
    )

    with pytest.raises(
        ClientAuthorizationError,
        match="User does not have access",
    ):
        await get_project_use_case(
            projects_db=projects_db,
            project_id="proj-999",
            user=user,
        )
