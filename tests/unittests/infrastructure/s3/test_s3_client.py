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

import base64
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from recnavi.infrastructure.s3 import s3_client
from recnavi.infrastructure.s3.s3_client import S3Client
from recnavi.infrastructure.s3.s3_client import delete_object_by_key
from recnavi.infrastructure.s3.s3_client import delete_objects_by_prefix
from recnavi.infrastructure.s3.s3_client import download_object
from recnavi.infrastructure.s3.s3_client import download_object_stream
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


class AsyncChunks:
    """Async iterable body yielding fixed chunks and supporting read()."""

    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        for chunk in self.chunks:
            yield chunk

    async def read(self) -> bytes:
        return b"".join(self.chunks)


def _patch_s3(mock_s3: MagicMock):
    """Patch aioboto3.Session so client() yields the given S3 mock."""
    mock_client_cm = MagicMock()
    mock_client_cm.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_client_cm.__aexit__ = AsyncMock(return_value=None)
    mock_session = MagicMock()
    mock_session.client = MagicMock(return_value=mock_client_cm)
    return patch(
        "recnavi.infrastructure.s3.s3_client.aioboto3.Session",
        return_value=mock_session,
    )


@pytest.mark.asyncio
async def test_upload_base64_decodes_and_puts_object():
    """Test upload_base64 stores decoded bytes with the content type."""
    mock_s3 = MagicMock()
    mock_s3.put_object = AsyncMock()

    with _patch_s3(mock_s3):
        await upload_base64(
            bucket_name="bucket",
            object_key="a/b.mp4",
            base64_data=base64.b64encode(b"payload").decode(),
            content_type="video/webm",
        )

    mock_s3.put_object.assert_awaited_once_with(
        Bucket="bucket",
        Key="a/b.mp4",
        Body=b"payload",
        ContentType="video/webm",
    )


@pytest.mark.asyncio
async def test_upload_base64_invalid_data_raises_value_error():
    """Test invalid base64 raises ValueError before touching S3."""
    with patch(
        "recnavi.infrastructure.s3.s3_client.aioboto3.Session",
    ) as mock_session_class:
        with pytest.raises(ValueError, match="Invalid base64 data"):
            await upload_base64(
                bucket_name="bucket",
                object_key="k",
                base64_data="abc",
            )

    mock_session_class.assert_not_called()


@pytest.mark.asyncio
async def test_download_object_returns_bytes():
    """Test download_object reads the whole body."""
    mock_s3 = MagicMock()
    mock_s3.get_object = AsyncMock(
        return_value={"Body": AsyncChunks([b"ab", b"cd"])},
    )

    with _patch_s3(mock_s3):
        data = await download_object(bucket_name="bucket", object_key="k")

    assert data == b"abcd"
    mock_s3.get_object.assert_awaited_once_with(Bucket="bucket", Key="k")


@pytest.mark.asyncio
async def test_download_object_stream_yields_chunks():
    """Test download_object_stream yields each body chunk."""
    mock_s3 = MagicMock()
    mock_s3.get_object = AsyncMock(
        return_value={"Body": AsyncChunks([b"ab", b"cd"])},
    )

    with _patch_s3(mock_s3):
        chunks = [
            chunk
            async for chunk in download_object_stream(
                bucket_name="bucket",
                object_key="k",
            )
        ]

    assert chunks == [b"ab", b"cd"]


@pytest.mark.asyncio
async def test_delete_objects_by_prefix_follows_pagination():
    """Test delete_objects_by_prefix deletes every page and counts keys."""
    mock_s3 = MagicMock()
    mock_s3.list_objects_v2 = AsyncMock(
        side_effect=[
            {
                "Contents": [{"Key": "p/1"}, {"Key": "p/2"}],
                "IsTruncated": True,
                "NextContinuationToken": "token",
            },
            {"Contents": [{"Key": "p/3"}], "IsTruncated": False},
        ],
    )
    mock_s3.delete_objects = AsyncMock()

    with _patch_s3(mock_s3):
        deleted = await delete_objects_by_prefix(
            bucket_name="bucket",
            prefix="p/",
        )

    assert deleted == 3
    assert mock_s3.delete_objects.await_count == 2
    second_list_call = mock_s3.list_objects_v2.await_args_list[1]
    assert second_list_call.kwargs["ContinuationToken"] == "token"


@pytest.mark.asyncio
async def test_delete_objects_by_prefix_returns_zero_when_empty():
    """Test delete_objects_by_prefix returns 0 when nothing matches."""
    mock_s3 = MagicMock()
    mock_s3.list_objects_v2 = AsyncMock(return_value={})
    mock_s3.delete_objects = AsyncMock()

    with _patch_s3(mock_s3):
        deleted = await delete_objects_by_prefix(
            bucket_name="bucket",
            prefix="p/",
        )

    assert deleted == 0
    mock_s3.delete_objects.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_object_by_key_deletes_exact_key():
    """Test delete_object_by_key uses S3's single-object operation."""
    mock_s3 = MagicMock()
    mock_s3.delete_object = AsyncMock()

    with _patch_s3(mock_s3):
        await delete_object_by_key(
            bucket_name="bucket",
            object_key="p/shot.mp4",
        )

    mock_s3.delete_object.assert_awaited_once_with(
        Bucket="bucket",
        Key="p/shot.mp4",
    )


@pytest.mark.asyncio
async def test_s3_client_delegates_async_methods_to_module_functions():
    """Test S3Client forwards each call to the module-level function."""
    client = S3Client()

    with (
        patch.object(s3_client, "upload_base64", AsyncMock()) as upload,
        patch.object(
            s3_client,
            "delete_objects_by_prefix",
            AsyncMock(return_value=2),
        ) as delete,
        patch.object(
            s3_client,
            "delete_object_by_key",
            AsyncMock(),
        ) as delete_one,
        patch.object(
            s3_client,
            "download_object",
            AsyncMock(return_value=b"x"),
        ) as download,
        patch.object(
            s3_client,
            "generate_presigned_url",
            AsyncMock(return_value="signed"),
        ) as presign,
    ):
        await client.upload_base64(
            bucket_name="b",
            object_key="k",
            base64_data="eA==",
            content_type="video/mp4",
        )
        deleted = await client.delete_objects_by_prefix(
            bucket_name="b",
            prefix="p/",
        )
        await client.delete_object_by_key(
            bucket_name="b",
            object_key="k",
        )
        data = await client.download_object(bucket_name="b", object_key="k")
        url = await client.generate_presigned_url(
            bucket_name="b",
            object_key="k",
            expiration=10,
        )

    upload.assert_awaited_once_with(
        bucket_name="b",
        object_key="k",
        base64_data="eA==",
        content_type="video/mp4",
    )
    delete.assert_awaited_once_with(bucket_name="b", prefix="p/")
    delete_one.assert_awaited_once_with(bucket_name="b", object_key="k")
    download.assert_awaited_once_with(bucket_name="b", object_key="k")
    presign.assert_awaited_once_with(
        bucket_name="b",
        object_key="k",
        expiration=10,
    )
    assert (deleted, data, url) == (2, b"x", "signed")


@pytest.mark.asyncio
async def test_s3_client_download_object_stream_delegates():
    """Test S3Client.download_object_stream returns the module stream."""

    async def fake_stream(*, bucket_name: str, object_key: str):
        yield f"{bucket_name}/{object_key}".encode()

    with patch.object(s3_client, "download_object_stream", fake_stream):
        chunks = [
            chunk
            async for chunk in S3Client().download_object_stream(
                bucket_name="b",
                object_key="k",
            )
        ]

    assert chunks == [b"b/k"]
