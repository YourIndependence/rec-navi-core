# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for download project use case."""

import io
import json
import zipfile
from unittest.mock import ANY
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.download_project_usecase import (
    download_project_usecase,
)
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


@pytest.mark.asyncio
async def test_download_project_usecase_creates_zip_with_videos_and_metadata():
    """Test usecase creates zip archive with videos and metadata.json."""
    owner = User(
        user_id="owner-1",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group-1",
    )

    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        description="Test Description",
        assigned_user_ids=["staff-1"],
        scenes=[
            Scene(
                scene_id="scene-1",
                scene_principal="cooking",
                status=SceneStatus.APPROVE,
                video_key="projects/proj-123/scenes/scene-1/shot-1.mp4",
                thumbnail_key="projects/proj-123/scenes/scene-1/shot-1_thumb.jpg",
                created_by="staff-1",
                created_at="2026-09-20T10:00:00Z",
                assigned_user_ids=["staff-1"],
            ),
            Scene(
                scene_id="scene-2",
                scene_principal="plating",
                status=SceneStatus.APPROVE,
                video_key="projects/proj-123/scenes/scene-2/shot-2.mp4",
                thumbnail_key="projects/proj-123/scenes/scene-2/shot-2_thumb.jpg",
                created_by="staff-1",
                created_at="2026-09-20T10:05:00Z",
                assigned_user_ids=["staff-1"],
            ),
        ],
        status=ProjectStatus.SUBMITTED,
        version=0,
        created_at="2026-09-20T09:00:00Z",
        updated_at="2026-09-20T10:10:00Z",
    )

    # Mock S3 functions
    mock_download_object = AsyncMock(
        side_effect=[
            b"fake video data 1",  # cooking video
            b"fake video data 2",  # plating video
        ],
    )
    mock_upload_base64 = AsyncMock()
    mock_generate_presigned_url = AsyncMock(
        return_value="https://test-bucket.s3.amazonaws.com/archives/test.zip?signature",
    )

    with (
        patch(
            "recnavi.application.project.download_project_usecase.download_object",
            mock_download_object,
        ),
        patch(
            "recnavi.application.project.download_project_usecase.upload_base64",
            mock_upload_base64,
        ),
        patch(
            "recnavi.application.project.download_project_usecase.generate_presigned_url",
            mock_generate_presigned_url,
        ),
    ):
        presigned_url = await download_project_usecase(
            user=owner,
            project=project,
            bucket_name="test-bucket",
        )

    assert (
        presigned_url
        == "https://test-bucket.s3.amazonaws.com/archives/test.zip?signature"
    )

    assert mock_download_object.call_count == 2
    mock_download_object.assert_any_call(
        bucket_name="test-bucket",
        object_key="projects/proj-123/scenes/scene-1/shot-1.mp4",
    )
    mock_download_object.assert_any_call(
        bucket_name="test-bucket",
        object_key="projects/proj-123/scenes/scene-2/shot-2.mp4",
    )

    mock_upload_base64.assert_called_once()
    upload_call_kwargs = mock_upload_base64.call_args[1]
    assert upload_call_kwargs["bucket_name"] == "test-bucket"
    assert upload_call_kwargs["object_key"] == "archives/proj-123.zip"
    assert upload_call_kwargs["content_type"] == "application/zip"

    import base64

    zip_bytes = base64.b64decode(upload_call_kwargs["base64_data"])
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "cooking.mp4" in namelist
        assert "plating.mp4" in namelist
        assert "metadata.json" in namelist

        assert zf.read("cooking.mp4") == b"fake video data 1"
        assert zf.read("plating.mp4") == b"fake video data 2"

        metadata_json = zf.read("metadata.json").decode("utf-8")
        metadata = json.loads(metadata_json)
        assert metadata["projectId"] == "proj-123"
        assert metadata["projectName"] == "Test Project"
        assert metadata["description"] == "Test Description"
        assert len(metadata["scenes"]) == 2
        assert metadata["scenes"][0]["scenePrincipal"] == "cooking"
        assert metadata["scenes"][0]["fileName"] == "cooking.mp4"
        assert metadata["scenes"][1]["scenePrincipal"] == "plating"
        assert metadata["scenes"][1]["fileName"] == "plating.mp4"

    mock_generate_presigned_url.assert_called_once_with(
        bucket_name="test-bucket",
        object_key="archives/proj-123.zip",
        expiration=3600,
    )


@pytest.mark.asyncio
async def test_download_project_usecase_handles_duplicate_scene_principals():
    """Test usecase handles duplicate scene principals with unique filenames."""
    owner = User(
        user_id="owner-1",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group-1",
    )

    project = Project(
        project_id="proj-456",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Duplicate Test",
        description="Test duplicate scene principals",
        assigned_user_ids=["staff-1"],
        scenes=[
            Scene(
                scene_id="scene-1",
                scene_principal="cooking",
                status=SceneStatus.APPROVE,
                video_key="projects/proj-456/scenes/scene-1/shot-1.mp4",
                thumbnail_key=None,
                created_by="staff-1",
                created_at="2026-09-20T10:00:00Z",
                assigned_user_ids=["staff-1"],
            ),
            Scene(
                scene_id="scene-2",
                scene_principal="cooking",  # Duplicate
                status=SceneStatus.APPROVE,
                video_key="projects/proj-456/scenes/scene-2/shot-2.mp4",
                thumbnail_key=None,
                created_by="staff-1",
                created_at="2026-09-20T10:05:00Z",
                assigned_user_ids=["staff-1"],
            ),
            Scene(
                scene_id="scene-3",
                scene_principal="cooking",  # Duplicate
                status=SceneStatus.APPROVE,
                video_key="projects/proj-456/scenes/scene-3/shot-3.mp4",
                thumbnail_key=None,
                created_by="staff-1",
                created_at="2026-09-20T10:10:00Z",
                assigned_user_ids=["staff-1"],
            ),
        ],
        status=ProjectStatus.SUBMITTED,
        version=0,
        created_at="2026-09-20T09:00:00Z",
        updated_at="2026-09-20T10:15:00Z",
    )

    # Mock S3 functions
    mock_download_object = AsyncMock(
        side_effect=[
            b"video 1",
            b"video 2",
            b"video 3",
        ],
    )
    mock_upload_base64 = AsyncMock()
    mock_generate_presigned_url = AsyncMock(
        return_value="https://test-bucket.s3.amazonaws.com/archives/test.zip",
    )

    with (
        patch(
            "recnavi.application.project.download_project_usecase.download_object",
            mock_download_object,
        ),
        patch(
            "recnavi.application.project.download_project_usecase.upload_base64",
            mock_upload_base64,
        ),
        patch(
            "recnavi.application.project.download_project_usecase.generate_presigned_url",
            mock_generate_presigned_url,
        ),
    ):
        await download_project_usecase(
            user=owner,
            project=project,
            bucket_name="test-bucket",
        )

    upload_call_kwargs = mock_upload_base64.call_args[1]

    import base64

    zip_bytes = base64.b64decode(upload_call_kwargs["base64_data"])
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "cooking.mp4" in namelist
        assert "cooking_2.mp4" in namelist
        assert "cooking_3.mp4" in namelist
        assert "metadata.json" in namelist

        metadata_json = zf.read("metadata.json").decode("utf-8")
        metadata = json.loads(metadata_json)
        assert metadata["scenes"][0]["fileName"] == "cooking.mp4"
        assert metadata["scenes"][1]["fileName"] == "cooking_2.mp4"
        assert metadata["scenes"][2]["fileName"] == "cooking_3.mp4"


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
    expected_output = "https://example.com/archive.zip"

    with patch(
        "recnavi.application.project.download_project_usecase.create_project_archive",
        new=AsyncMock(return_value=expected_output),
    ) as mock_create:
        result = await download_project_usecase(
            user=user,
            project=project,
            bucket_name="test-bucket",
        )

    mock_create.assert_awaited_once_with(
        user=user,
        project=project,
        bucket_name="test-bucket",
        download_video=ANY,
        upload_archive=ANY,
        generate_url=ANY,
    )
    assert result is expected_output
