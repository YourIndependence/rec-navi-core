# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for update_scene_record_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from mockups.mock_database import MockDatabase

from recnavi.application.scene.update_scene_record_usecase import (
    update_scene_record_usecase,
)
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


@pytest.mark.asyncio
async def test_usecase_uploads_video_and_thumbnail_to_s3():
    """Test usecase uploads both video and thumbnail to S3."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-123",
                "groupId": "group-456",
                "projectName": "Test Project",
                "ownerUserId": "owner-1",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-1",
                        "scenePrincipal": "cooking",
                        "videoKey": None,
                        "assignedUserIds": ["staff-789"],
                    },
                ],
            },
        ],
    )

    staff = User(
        user_id="staff-789",
        user_name="Staff",
        group_id="group-456",
        role=UserRole.STAFF,
    )

    with patch(
        "recnavi.application.scene.update_scene_record_usecase.upload_base64",
    ) as mock_upload:
        mock_upload.return_value = AsyncMock()

        await update_scene_record_usecase(
            projects_db=database,
            project_id="proj-123",
            scene_id="scene-1",
            video_base64="ZmFrZSB2aWRlbyBkYXRh",
            thumbnail_base64="ZmFrZSB0aHVtYm5haWw=",
            user=staff,
            video_bucket_name="test-bucket",
        )

    assert mock_upload.call_count == 2

    video_call = mock_upload.call_args_list[0]
    assert video_call[1]["content_type"] == "video/mp4"
    assert video_call[1]["base64_data"] == "ZmFrZSB2aWRlbyBkYXRh"

    thumbnail_call = mock_upload.call_args_list[1]
    assert thumbnail_call[1]["content_type"] == "image/jpeg"
    assert thumbnail_call[1]["base64_data"] == "ZmFrZSB0aHVtYm5haWw="


@pytest.mark.asyncio
async def test_usecase_updates_dynamodb_with_condition():
    """Test usecase updates DynamoDB with condition expression."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-456",
                "groupId": "group-789",
                "projectName": "Test Project 2",
                "ownerUserId": "owner-2",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-2",
                        "scenePrincipal": "interview",
                        "status": "not_recorded",
                        "videoKey": None,
                        "assignedUserIds": ["staff-001"],
                    },
                ],
            },
        ],
    )

    staff = User(
        user_id="staff-001",
        user_name="Staff",
        group_id="group-789",
        role=UserRole.STAFF,
    )

    with patch(
        "recnavi.application.scene.update_scene_record_usecase.upload_base64",
    ):
        with patch(
            "recnavi.application.scene.update_scene_record_usecase.delete_objects_by_prefix",
        ):
            await update_scene_record_usecase(
                projects_db=database,
                project_id="proj-456",
                scene_id="scene-2",
                video_base64="dmlkZW8=",
                thumbnail_base64="dGh1bWI=",
                user=staff,
                video_bucket_name="test-bucket",
            )

    updated_item = await database.get_item({"projectId": "proj-456"})
    assert updated_item["scenes"][0]["status"] == SceneStatus.PENDING.value
    assert updated_item["scenes"][0]["videoKey"] is not None
    assert updated_item["scenes"][0]["thumbnailKey"] is not None
    assert updated_item["scenes"][0]["createdBy"] == "staff-001"
    assert updated_item["scenes"][0]["createdAt"] is not None


@pytest.mark.asyncio
async def test_usecase_deletes_old_shot_when_exists():
    """Test usecase deletes old shot when scene has existing video."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-999",
                "groupId": "group-abc",
                "projectName": "Test Project 3",
                "ownerUserId": "owner-3",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-3",
                        "scenePrincipal": "product-shot",
                        "videoKey": "projects/proj-999/scenes/scene-3/old-shot-123.mp4",
                        "assignedUserIds": ["staff-002"],
                    },
                ],
            },
        ],
    )

    staff = User(
        user_id="staff-002",
        user_name="Staff",
        group_id="group-abc",
        role=UserRole.STAFF,
    )

    with patch(
        "recnavi.application.scene.update_scene_record_usecase.upload_base64",
    ):
        with patch(
            "recnavi.application.scene.update_scene_record_usecase.delete_objects_by_prefix",
        ) as mock_delete:
            mock_delete.return_value = AsyncMock()

            await update_scene_record_usecase(
                projects_db=database,
                project_id="proj-999",
                scene_id="scene-3",
                video_base64="dmlkZW8=",
                thumbnail_base64="dGh1bWI=",
                user=staff,
                video_bucket_name="test-bucket",
            )

    mock_delete.assert_called_once()
    call_kwargs = mock_delete.call_args[1]
    assert call_kwargs["bucket_name"] == "test-bucket"
    assert "old-shot-123" in call_kwargs["prefix"]


@pytest.mark.asyncio
async def test_usecase_skips_deletion_on_first_recording():
    """Test usecase skips S3 deletion when no previous recording exists."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-111",
                "groupId": "group-222",
                "projectName": "Test Project 4",
                "ownerUserId": "owner-4",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-4",
                        "scenePrincipal": "first-recording",
                        "videoKey": None,
                        "assignedUserIds": ["staff-003"],
                    },
                ],
            },
        ],
    )

    staff = User(
        user_id="staff-003",
        user_name="Staff",
        group_id="group-222",
        role=UserRole.STAFF,
    )

    with patch(
        "recnavi.application.scene.update_scene_record_usecase.upload_base64",
    ):
        with patch(
            "recnavi.application.scene.update_scene_record_usecase.delete_objects_by_prefix",
        ) as mock_delete:
            await update_scene_record_usecase(
                projects_db=database,
                project_id="proj-111",
                scene_id="scene-4",
                video_base64="dmlkZW8=",
                thumbnail_base64="dGh1bWI=",
                user=staff,
                video_bucket_name="test-bucket",
            )

    mock_delete.assert_not_called()


@pytest.mark.asyncio
async def test_usecase_returns_updated_project():
    """Test usecase returns updated project with PENDING status."""
    database = MockDatabase(
        initial_items=[
            {
                "projectId": "proj-555",
                "groupId": "group-666",
                "projectName": "Test Project 5",
                "ownerUserId": "owner-5",
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-01-01T00:00:00Z",
                "scenes": [
                    {
                        "sceneId": "scene-5",
                        "scenePrincipal": "return-test",
                        "status": "not_recorded",
                        "videoKey": None,
                        "assignedUserIds": ["staff-004"],
                    },
                ],
            },
        ],
    )

    staff = User(
        user_id="staff-004",
        user_name="Staff",
        group_id="group-666",
        role=UserRole.STAFF,
    )

    with patch(
        "recnavi.application.scene.update_scene_record_usecase.upload_base64",
    ):
        with patch(
            "recnavi.application.scene.update_scene_record_usecase.delete_objects_by_prefix",
        ):
            result = await update_scene_record_usecase(
                projects_db=database,
                project_id="proj-555",
                scene_id="scene-5",
                video_base64="dmlkZW8=",
                thumbnail_base64="dGh1bWI=",
                user=staff,
                video_bucket_name="test-bucket",
            )

    assert result.project_id == "proj-555"
    assert result.scenes[0].status == SceneStatus.PENDING
    assert result.scenes[0].video_key is not None
    assert result.scenes[0].thumbnail_key is not None
