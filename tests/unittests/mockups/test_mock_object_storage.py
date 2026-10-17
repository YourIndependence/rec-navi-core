# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for the shared MockObjectStorage."""

import base64

import pytest

from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_delete_exact_key_preserves_other_keys_and_buckets():
    """Delete only the exact object and allow repeated deletion."""
    storage = MockObjectStorage(bucket_name="b")
    storage.objects = {
        ("b", "video.mp4"): (b"video", "video/mp4"),
        ("b", "video.mp4.backup"): (b"backup", "video/mp4"),
        ("other", "video.mp4"): (b"other", "video/mp4"),
    }
    await storage.delete_object_by_key(object_key="video.mp4")
    await storage.delete_object_by_key(object_key="video.mp4")
    assert storage.objects == {
        ("b", "video.mp4.backup"): (b"backup", "video/mp4"),
        ("other", "video.mp4"): (b"other", "video/mp4"),
    }


@pytest.mark.asyncio
async def test_delete_prefix_without_matches_returns_zero():
    """Preserve unrelated data when the requested prefix is absent."""
    storage = MockObjectStorage(bucket_name="b")
    storage.objects[("b", "keep")] = (b"keep", "video/mp4")
    assert await storage.delete_objects_by_prefix(prefix="missing/") == 0
    assert storage.objects == {("b", "keep"): (b"keep", "video/mp4")}


@pytest.mark.asyncio
async def test_upload_then_download_round_trip():
    """Test uploaded base64 content is stored decoded."""
    storage = MockObjectStorage(bucket_name="b")
    payload = base64.b64encode(b"video-bytes").decode()

    await storage.upload_base64(
        object_key="k.mp4",
        base64_data=payload,
        content_type="video/mp4",
    )

    assert await storage.download_object(
        object_key="k.mp4",
    ) == (b"video-bytes")
    assert storage.objects[("b", "k.mp4")][1] == "video/mp4"


@pytest.mark.asyncio
async def test_upload_invalid_base64_raises_value_error():
    """Test invalid base64 data raises ValueError."""
    storage = MockObjectStorage(bucket_name="b")

    with pytest.raises(ValueError, match="Invalid base64 data"):
        await storage.upload_base64(
            object_key="k",
            base64_data="not base64!!",
            content_type="video/mp4",
        )


@pytest.mark.asyncio
async def test_download_object_stream_yields_stored_bytes():
    """Test download_object_stream yields the stored content."""
    storage = MockObjectStorage(bucket_name="b")
    storage.objects[("b", "k")] = (b"abc", "image/png")

    chunks = [
        chunk
        async for chunk in storage.download_object_stream(
            object_key="k",
        )
    ]

    assert b"".join(chunks) == b"abc"


@pytest.mark.asyncio
async def test_delete_objects_by_prefix_counts_only_matches():
    """Test only objects under the prefix and bucket are deleted."""
    storage = MockObjectStorage(bucket_name="b")
    storage.objects[("b", "p/1")] = (b"1", "x")
    storage.objects[("b", "p/2")] = (b"2", "x")
    storage.objects[("b", "q/1")] = (b"3", "x")
    storage.objects[("other", "p/1")] = (b"4", "x")

    deleted = await storage.delete_objects_by_prefix(
        prefix="p/",
    )

    assert deleted == 2
    assert set(storage.objects) == {("b", "q/1"), ("other", "p/1")}


@pytest.mark.asyncio
async def test_generate_presigned_url_is_deterministic_and_not_https():
    """Test the fake URL embeds bucket, key and expiration."""
    url = await MockObjectStorage(bucket_name="b").generate_presigned_url(
        object_key="k",
        expiration=60,
    )

    assert url == "mock://b/k?expires=60"
