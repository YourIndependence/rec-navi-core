# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_project_view and create_project_view."""

import pytest

from recnavi.core.project.project_view import create_project_view
from recnavi.core.project.project_view import get_project_view
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.fixture
def owner() -> User:
    """Provide the account owner used by every test."""
    return User(
        user_id="user-789",
        user_name="Owner",
        group_id="group-456",
        role=UserRole.OWNER,
    )


@pytest.mark.asyncio
async def test_get_project_view_returns_presigned_urls(owner: User):
    """get_project_view loads the project and presigns recorded scenes."""
    projects_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-123",
                "groupId": "group-456",
                "projectName": "Test Project",
                "ownerUserId": "user-789",
                "createdAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "s1",
                        "scenePrincipal": "opening",
                        "videoKey": "videos/s1.mp4",
                    },
                ],
            },
        ],
    )

    view = await get_project_view(
        projects_db=projects_db,
        storage=MockObjectStorage(),
        bucket_name="bucket",
        project_id="proj-123",
        user=owner,
    )

    assert view.project_id == "proj-123"
    assert view.scenes[0].video_url is not None
    assert view.scenes[0].thumbnail_url is None


@pytest.mark.asyncio
async def test_create_project_view_returns_scenes_without_urls(owner: User):
    """create_project_view returns new unrecorded scenes with null URLs."""
    view = await create_project_view(
        projects_db=MockDatabase(),
        storage=MockObjectStorage(),
        bucket_name="bucket",
        project_name="New",
        description="",
        scene_principals=["opening", "main"],
        assigned_user_ids=[],
        owner=owner,
    )

    assert len(view.scenes) == 2
    assert all(s.video_url is None for s in view.scenes)
    assert all(s.thumbnail_url is None for s in view.scenes)
