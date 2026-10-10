# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for scene master core logic."""

import pytest

from recnavi.core.scene.scene_master import get_scene_masters
from recnavi.core.scene.scene_master import get_scene_thumbnail
from recnavi.exceptions.exceptions import ClientResourcesNotFoundError
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


async def _collect(stream) -> bytes:
    return b"".join([chunk async for chunk in stream])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kind", "object_key", "content_type"),
    [
        ("example", "scenes/cooking/example.jpg", "image/jpeg"),
        ("guide", "scenes/cooking/guide.png", "image/png"),
    ],
)
async def test_get_scene_thumbnail_streams_object(
    kind,
    object_key,
    content_type,
):
    """Test core streams the stored object with inferred content type."""
    storage = MockObjectStorage()
    storage.objects[("test-bucket", object_key)] = (b"bytes", content_type)

    stream, actual_type = await get_scene_thumbnail(
        scenes_db=_thumbnail_db(),
        scene_principal="cooking",
        kind=kind,
        bucket_name="test-bucket",
        storage=storage,
    )

    assert await _collect(stream) == b"bytes"
    assert actual_type == content_type


@pytest.mark.asyncio
async def test_get_scene_thumbnail_raises_404_when_scene_not_found():
    """Test core raises ClientResourcesNotFoundError for unknown scene."""
    with pytest.raises(ClientResourcesNotFoundError):
        await get_scene_thumbnail(
            scenes_db=MockDatabase(initial_items=[]),
            scene_principal="nonexistent",
            kind="example",
            bucket_name="test-bucket",
            storage=MockObjectStorage(),
        )


@pytest.mark.asyncio
async def test_get_scene_thumbnail_raises_422_for_invalid_kind():
    """Test core raises ClientUnprocessableEntityError for invalid kind."""
    with pytest.raises(ClientUnprocessableEntityError):
        await get_scene_thumbnail(
            scenes_db=_thumbnail_db(),
            scene_principal="cooking",
            kind="invalid_kind",
            bucket_name="test-bucket",
            storage=MockObjectStorage(),
        )
