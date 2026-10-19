# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for scene master core logic."""

from unittest.mock import AsyncMock

import pytest

from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.core.scene.scene_master import get_scene_masters
from recnavi.core.scene.scene_master import get_scene_thumbnail
from recnavi.core.types.database import DatabaseQueryResult
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_get_scene_masters_returns_all_scenes():
    """Test get_scene_masters returns all scene masters from database."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "scenePrincipal": "shop_gaikan",
                "title": "Shop Exterior",
                "thumbnailUri": "s3://bucket/shop_gaikan_thumb.jpg",
                "guideUri": "s3://bucket/shop_gaikan_guide.jpg",
                "maxDurationSeconds": 30,
            },
            {
                "scenePrincipal": "staff_intro",
                "title": "Staff Introduction",
                "thumbnailUri": "s3://bucket/staff_intro_thumb.jpg",
                "guideUri": "s3://bucket/staff_intro_guide.jpg",
                "maxDurationSeconds": 15,
            },
        ],
    )

    result = await get_scene_masters(scenes_db=mock_db)

    assert len(result) == 2
    assert result[0].scene_principal == "shop_gaikan"
    assert result[0].title == "Shop Exterior"
    assert result[0].max_duration_seconds == 30
    assert result[1].scene_principal == "staff_intro"
    assert result[1].title == "Staff Introduction"
    assert result[1].max_duration_seconds == 15


@pytest.mark.asyncio
async def test_get_scene_masters_returns_empty_list_when_no_scenes():
    """Test get_scene_masters returns empty list when database is empty."""
    mock_db = MockDatabase(initial_items=[])

    result = await get_scene_masters(scenes_db=mock_db)

    assert result == []


@pytest.mark.asyncio
async def test_get_scene_masters_handles_many_scenes():
    """Test get_scene_masters handles multiple scene masters correctly."""
    scenes = [
        {
            "scenePrincipal": f"scene_{i}",
            "title": f"Scene {i}",
            "thumbnailUri": f"s3://bucket/scene_{i}_thumb.jpg",
            "guideUri": f"s3://bucket/scene_{i}_guide.jpg",
            "maxDurationSeconds": 10 + i,
        }
        for i in range(50)
    ]
    mock_db = MockDatabase(initial_items=scenes)

    result = await get_scene_masters(scenes_db=mock_db)

    assert len(result) == 50
    assert result[0].scene_principal == "scene_0"
    assert result[49].scene_principal == "scene_49"
    assert result[49].max_duration_seconds == 59


def _thumbnail_db() -> MockDatabase:
    return MockDatabase(
        initial_items=[
            {
                "scenePrincipal": "cooking",
                "title": "Cooking Scene",
                "thumbnailUri": "scenes/cooking/example.jpg",
                "guideUri": "scenes/cooking/guide.png",
                "maxDurationSeconds": 60,
            },
        ],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kind", "object_key", "content_type"),
    [
        ("example", "scenes/cooking/example.jpg", "image/jpeg"),
        ("guide", "scenes/cooking/guide.png", "image/png"),
    ],
)
async def test_get_scene_thumbnail_downloads_object(
    kind,
    object_key,
    content_type,
):
    """Test core downloads the stored object with inferred content type."""
    storage = MockObjectStorage(bucket_name="test-bucket")
    storage.objects[("test-bucket", object_key)] = (b"bytes", content_type)

    stream, actual_type = await get_scene_thumbnail(
        scenes_db=_thumbnail_db(),
        scene_principal="cooking",
        kind=kind,
        storage=storage,
    )

    assert stream == b"bytes"
    assert actual_type == content_type


@pytest.mark.asyncio
async def test_get_scene_thumbnail_raises_404_when_scene_not_found():
    """Test core raises ClientNotFoundError for unknown scene."""
    with pytest.raises(ClientNotFoundError):
        await get_scene_thumbnail(
            scenes_db=MockDatabase(initial_items=[]),
            scene_principal="nonexistent",
            kind="example",
            storage=MockObjectStorage(bucket_name="test-bucket"),
        )


@pytest.mark.asyncio
async def test_get_scene_thumbnail_raises_422_for_invalid_kind():
    """Test core raises ClientUnprocessableEntityError for invalid kind."""
    with pytest.raises(ClientUnprocessableEntityError):
        await get_scene_thumbnail(
            scenes_db=_thumbnail_db(),
            scene_principal="cooking",
            kind="invalid_kind",
            storage=MockObjectStorage(bucket_name="test-bucket"),
        )


@pytest.mark.asyncio
async def test_thumbnail_queries_scene_by_principal():
    database = AsyncMock()
    item = (await _thumbnail_db().scan()).items[0]
    database.query.return_value = DatabaseQueryResult(items=[item])
    storage = MockObjectStorage(bucket_name="test-bucket")
    storage.objects[("test-bucket", "scenes/cooking/example.jpg")] = (
        b"image",
        "image/jpeg",
    )
    assert await get_scene_thumbnail(
        scenes_db=database,
        scene_principal="cooking",
        kind="example",
        storage=storage,
    ) == (b"image", "image/jpeg")
    database.query.assert_awaited_once_with(
        key_condition={"scenePrincipal": "cooking"},
        limit=1,
    )
    database.scan.assert_not_awaited()


@pytest.mark.asyncio
async def test_thumbnail_resolves_configured_bucket_uri():
    item = (await _thumbnail_db().scan()).items[0]
    item["thumbnailUri"] = (
        f"s3://{MEDIA_BUCKET_NAME}/scenes/cooking/example.jpg"
    )
    storage = MockObjectStorage(bucket_name=MEDIA_BUCKET_NAME)
    storage.objects[(MEDIA_BUCKET_NAME, "scenes/cooking/example.jpg")] = (
        b"image",
        "image/jpeg",
    )
    assert await get_scene_thumbnail(
        scenes_db=MockDatabase(initial_items=[item]),
        scene_principal="cooking",
        kind="example",
        storage=storage,
    ) == (b"image", "image/jpeg")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "uri",
    [
        "s3://other-bucket/image.jpg",
        "https://example.org/image.jpg",
        "image.svg",
    ],
)
async def test_thumbnail_rejects_external_bucket_and_unsupported_images(uri):
    item = (await _thumbnail_db().scan()).items[0]
    item["thumbnailUri"] = uri
    with pytest.raises(ClientUnprocessableEntityError):
        await get_scene_thumbnail(
            scenes_db=MockDatabase(initial_items=[item]),
            scene_principal="cooking",
            kind="example",
            storage=MockObjectStorage(bucket_name="test-bucket"),
        )
