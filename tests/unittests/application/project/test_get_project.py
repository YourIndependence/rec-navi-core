# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_project use case."""

from unittest.mock import patch

import pytest

from recnavi.application.project.get_project import get_project_use_case
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.exceptions.exceptions import ClientAuthorizationError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_project_use_case_returns_project_with_urls():
    """Test get_project_use_case returns Project and presigned URLs."""
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
        role="owner",
        email="test@test.com",
        phone_number="000-0000-0000",
        birthday="1990-01-01",
        profile_image_uri="s3://bucket/profile.jpg",
    )

    with patch(
        "recnavi.application.project.get_project.generate_presigned_url",
    ) as mock_generate_url:
        mock_generate_url.side_effect = lambda bucket_name, object_key: (
            f"https://example.com/{object_key}?signature=abc123"
        )

        project, scene_urls = await get_project_use_case(
            projects_db=projects_db,
            project_id="proj-123",
            user=user,
            video_bucket_name="test-bucket",
        )

    assert isinstance(project, Project)
    assert project.project_id == "proj-123"
    assert project.group_id == "group-456"
    assert project.version == 1

    assert len(project.scenes) == 1
    assert "scene-001" in scene_urls
    assert (
        scene_urls["scene-001"]["video_url"]
        == "https://example.com/videos/scene-001.mp4?signature=abc123"
    )
    assert (
        scene_urls["scene-001"]["thumbnail_url"]
        == "https://example.com/thumbnails/scene-001.jpg?signature=abc123"
    )

    assert mock_generate_url.call_count == 2


@pytest.mark.asyncio
async def test_get_project_use_case_handles_missing_video_keys():
    """Test get_project_use_case handles scenes without video/thumbnail keys."""
    projects_db = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-456",
                "groupId": "group-789",
                "projectName": "Empty Project",
                "description": "",
                "ownerUserId": "user-001",
                "assignedUserIds": [],
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "status": "in_progress",
                "version": 1,
                "scenes": [
                    {
                        "sceneId": "scene-002",
                        "scenePrincipal": "closing",
                        "status": "not_recorded",
                        "videoKey": None,
                        "thumbnailKey": None,
                        "createdBy": None,
                        "createdAt": None,
                        "assignedAt": None,
                        "assignedUserIds": [],
                    },
                ],
            },
        ],
    )

    user = User(
        user_id="user-001",
        user_name="Owner",
        group_id="group-789",
        role="owner",
        email="owner@test.com",
        phone_number="000-0000-0001",
        birthday="1991-01-01",
        profile_image_uri="s3://bucket/owner.jpg",
    )

    with patch(
        "recnavi.application.project.get_project.generate_presigned_url",
    ) as mock_generate_url:
        project, scene_urls = await get_project_use_case(
            projects_db=projects_db,
            project_id="proj-456",
            user=user,
            video_bucket_name="test-bucket",
        )

    assert isinstance(project, Project)
    assert len(project.scenes) == 1
    assert "scene-002" in scene_urls
    assert scene_urls["scene-002"]["video_url"] is None
    assert scene_urls["scene-002"]["thumbnail_url"] is None

    mock_generate_url.assert_not_called()


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
        group_id="group-bbb",  # Different group
        role="owner",
        email="bbb@test.com",
        phone_number="000-0000-0002",
        birthday="1992-01-01",
        profile_image_uri="s3://bucket/bbb.jpg",
    )

    with pytest.raises(
        ClientAuthorizationError,
        match="Access to other group's project",
    ):
        await get_project_use_case(
            projects_db=projects_db,
            project_id="proj-999",
            user=user,
            video_bucket_name="test-bucket",
        )
