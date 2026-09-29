# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for S3 client operations."""

import base64
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from recnavi.infrastructure.s3.s3_client import delete_objects_by_prefix
from recnavi.infrastructure.s3.s3_client import generate_presigned_url
from recnavi.infrastructure.s3.s3_client import upload_base64


@pytest.mark.asyncio
async def test_generate_presigned_url_calls_boto3_correctly():
    """Test generate_presigned_url calls boto3 generate_presigned_url with correct params."""
    mock_url = "https://test-bucket.s3.ap-northeast-1.amazonaws.com/videos/scene-123.mp4?signature"

    # Create a mock client that supports async context manager
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url = MagicMock(return_value=mock_url)

    # Mock the session and client
    with patch(
        "recnavi.infrastructure.s3.s3_client.aioboto3.Session",
    ) as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Create mock async context manager for client
        mock_client_cm = MagicMock()
        mock_client_cm.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_client_cm.__aexit__ = AsyncMock(return_value=None)

        # Make client() return the context manager
        mock_session.client = MagicMock(return_value=mock_client_cm)

        # Call function under test
        url = await generate_presigned_url(
            bucket_name="test-bucket",
            object_key="videos/scene-123.mp4",
        )

        assert url == mock_url

        mock_session.client.assert_called_once_with(
            "s3",
            region_name="ap-northeast-1",
        )
        mock_s3.generate_presigned_url.assert_called_once_with(
            ClientMethod="get_object",
            Params={"Bucket": "test-bucket", "Key": "videos/scene-123.mp4"},
            ExpiresIn=3600,
        )


@pytest.mark.asyncio
async def test_generate_presigned_url_respects_custom_expiration():
    """Test generate_presigned_url passes custom expiration to boto3."""
    mock_url = "https://test-bucket.s3.ap-northeast-1.amazonaws.com/videos/scene-456.mp4"

    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url = MagicMock(return_value=mock_url)

    with patch(
        "recnavi.infrastructure.s3.s3_client.aioboto3.Session",
    ) as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_client_cm = MagicMock()
        mock_client_cm.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_client_cm.__aexit__ = AsyncMock(return_value=None)

        mock_session.client = MagicMock(return_value=mock_client_cm)

        url = await generate_presigned_url(
            bucket_name="test-bucket",
            object_key="videos/scene-456.mp4",
            expiration=7200,
        )

        assert url == mock_url
        mock_s3.generate_presigned_url.assert_called_once_with(
            ClientMethod="get_object",
            Params={"Bucket": "test-bucket", "Key": "videos/scene-456.mp4"},
            ExpiresIn=7200,  # Custom expiration
        )


@pytest.mark.asyncio
async def test_delete_objects_by_prefix_deletes_multiple_objects():
    """Test delete_objects_by_prefix deletes all objects under prefix."""
    mock_objects_page1 = {
        "Contents": [
            {"Key": "projects/proj-123/scenes/scene-1.mp4"},
            {"Key": "projects/proj-123/scenes/scene-1-thumb.jpg"},
            {"Key": "projects/proj-123/scenes/scene-2.mp4"},
        ],
        "IsTruncated": False,
    }

    mock_s3 = AsyncMock()
    mock_s3.list_objects_v2 = AsyncMock(return_value=mock_objects_page1)
    mock_s3.delete_objects = AsyncMock()

    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_client_cm.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "recnavi.infrastructure.s3.s3_client.aioboto3.Session",
    ) as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client = MagicMock(return_value=mock_client_cm)

        deleted_count = await delete_objects_by_prefix(
            bucket_name="test-bucket",
            prefix="projects/proj-123/",
        )

    assert deleted_count == 3
    mock_s3.list_objects_v2.assert_called_once_with(
        Bucket="test-bucket",
        Prefix="projects/proj-123/",
    )
    mock_s3.delete_objects.assert_called_once()
    call_args = mock_s3.delete_objects.call_args
    assert call_args[1]["Bucket"] == "test-bucket"
    assert len(call_args[1]["Delete"]["Objects"]) == 3


@pytest.mark.asyncio
async def test_delete_objects_by_prefix_returns_zero_when_empty():
    """Test delete_objects_by_prefix returns 0 when prefix has no objects."""
    mock_empty_response = {
        "Contents": [],
        "IsTruncated": False,
    }

    mock_s3 = AsyncMock()
    mock_s3.list_objects_v2 = AsyncMock(return_value=mock_empty_response)

    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_client_cm.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "recnavi.infrastructure.s3.s3_client.aioboto3.Session",
    ) as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client = MagicMock(return_value=mock_client_cm)

        deleted_count = await delete_objects_by_prefix(
            bucket_name="test-bucket",
            prefix="projects/nonexistent/",
        )

    assert deleted_count == 0
    mock_s3.list_objects_v2.assert_called_once()
    mock_s3.delete_objects.assert_not_called()


@pytest.mark.asyncio
async def test_delete_objects_by_prefix_handles_pagination():
    """Test delete_objects_by_prefix handles pagination for 1000+ objects."""
    mock_page1 = {
        "Contents": [
            {"Key": f"projects/proj-999/file-{i:04d}.txt"} for i in range(1000)
        ],
        "IsTruncated": True,
        "NextContinuationToken": "token-1",
    }
    mock_page2 = {
        "Contents": [
            {"Key": f"projects/proj-999/file-{i:04d}.txt"}
            for i in range(1000, 1500)
        ],
        "IsTruncated": False,
    }

    mock_s3 = AsyncMock()
    mock_s3.list_objects_v2 = AsyncMock(side_effect=[mock_page1, mock_page2])
    mock_s3.delete_objects = AsyncMock()

    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_client_cm.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "recnavi.infrastructure.s3.s3_client.aioboto3.Session",
    ) as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client = MagicMock(return_value=mock_client_cm)

        deleted_count = await delete_objects_by_prefix(
            bucket_name="test-bucket",
            prefix="projects/proj-999/",
        )

    assert deleted_count == 1500
    assert mock_s3.list_objects_v2.call_count == 2
    assert mock_s3.delete_objects.call_count == 2

    first_list_call = mock_s3.list_objects_v2.call_args_list[0]
    assert first_list_call[1]["Bucket"] == "test-bucket"
    assert first_list_call[1]["Prefix"] == "projects/proj-999/"
    assert "ContinuationToken" not in first_list_call[1]

    second_list_call = mock_s3.list_objects_v2.call_args_list[1]
    assert second_list_call[1]["ContinuationToken"] == "token-1"


@pytest.mark.asyncio
async def test_upload_base64_calls_put_object_with_decoded_data():
    """Test upload_base64 decodes base64 and calls put_object."""
    test_data = b"fake video data"
    base64_data = base64.b64encode(test_data).decode("utf-8")

    mock_s3 = AsyncMock()
    mock_s3.put_object = AsyncMock()

    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_client_cm.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "recnavi.infrastructure.s3.s3_client.aioboto3.Session",
    ) as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client = MagicMock(return_value=mock_client_cm)

        await upload_base64(
            bucket_name="test-bucket",
            object_key="projects/proj-123/scenes/scene-1/shot-abc.mp4",
            base64_data=base64_data,
            content_type="video/mp4",
        )

    mock_s3.put_object.assert_called_once()
    call_kwargs = mock_s3.put_object.call_args[1]
    assert call_kwargs["Bucket"] == "test-bucket"
    assert (
        call_kwargs["Key"] == "projects/proj-123/scenes/scene-1/shot-abc.mp4"
    )
    assert call_kwargs["Body"] == test_data
    assert call_kwargs["ContentType"] == "video/mp4"


@pytest.mark.asyncio
async def test_upload_base64_sets_content_type_correctly():
    """Test upload_base64 respects content_type parameter."""
    test_data = b"fake thumbnail"
    base64_data = base64.b64encode(test_data).decode("utf-8")

    mock_s3 = AsyncMock()
    mock_s3.put_object = AsyncMock()

    mock_client_cm = AsyncMock()
    mock_client_cm.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_client_cm.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "recnavi.infrastructure.s3.s3_client.aioboto3.Session",
    ) as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.client = MagicMock(return_value=mock_client_cm)

        await upload_base64(
            bucket_name="test-bucket",
            object_key="thumbnail.jpg",
            base64_data=base64_data,
            content_type="image/jpeg",
        )

    call_kwargs = mock_s3.put_object.call_args[1]
    assert call_kwargs["ContentType"] == "image/jpeg"


@pytest.mark.asyncio
async def test_upload_base64_raises_value_error_on_invalid_base64():
    """Test upload_base64 raises ValueError for invalid base64 data."""
    with pytest.raises(ValueError, match="Invalid base64 data"):
        await upload_base64(
            bucket_name="test-bucket",
            object_key="test.mp4",
            base64_data="not-valid-base64!!!",
            content_type="video/mp4",
        )
