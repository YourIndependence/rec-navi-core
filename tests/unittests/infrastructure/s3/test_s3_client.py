# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for S3 client presigned URL generation.

These are smoke tests verifying the function signature and basic structure.
Full integration testing with real/mocked S3 is covered in integration tests.
"""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from recnavi.infrastructure.s3.s3_client import generate_presigned_url


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
