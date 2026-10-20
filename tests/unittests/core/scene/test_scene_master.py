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

from recnavi.core.scene.scene_master import attach_scene_master_urls
from recnavi.core.scene.scene_master import get_scene_masters
from tests.mockups.mock_database import MockDatabase


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
                "maxDurationSeconds": 5,
            },
            {
                "scenePrincipal": "staff_intro",
                "title": "Staff Introduction",
                "thumbnailUri": "s3://bucket/staff_intro_thumb.jpg",
                "guideUri": "s3://bucket/staff_intro_guide.jpg",
                "maxDurationSeconds": 5,
            },
        ],
    )

    result = await get_scene_masters(scenes_db=mock_db)

    assert len(result) == 2
    assert result[0].scene_principal == "shop_gaikan"
    assert result[0].title == "Shop Exterior"
    assert result[0].max_duration_seconds == 5
    assert result[1].scene_principal == "staff_intro"
    assert result[1].title == "Staff Introduction"
    assert result[1].max_duration_seconds == 5


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
            "maxDurationSeconds": 1 + i % 10,
        }
        for i in range(50)
    ]
    mock_db = MockDatabase(initial_items=scenes)

    result = await get_scene_masters(scenes_db=mock_db)

    assert len(result) == 50
    assert result[0].scene_principal == "scene_0"
    assert result[49].scene_principal == "scene_49"
    assert result[49].max_duration_seconds == 10


@pytest.mark.asyncio
async def test_scene_master_images_are_presigned_without_storage_uris():
    database = MockDatabase(
        initial_items=[
            {
                "scenePrincipal": "cooking",
                "title": "Cooking",
                "thumbnailUri": "masters/cooking.jpg",
                "guideUri": "masters/cooking.png",
                "maxDurationSeconds": 5,
            },
        ],
    )
    storage = AsyncMock()
    storage.generate_presigned_url.side_effect = [
        "https://signed/thumbnail",
        "https://signed/guide",
    ]
    result = await attach_scene_master_urls(
        scenes=await get_scene_masters(scenes_db=database),
        storage=storage,
    )
    assert result[0].model_dump(by_alias=True) == {
        "scenePrincipal": "cooking",
        "title": "Cooking",
        "maxDurationSeconds": 5,
        "thumbnailUrl": "https://signed/thumbnail",
        "guideUrl": "https://signed/guide",
    }
    assert [
        call.kwargs for call in storage.generate_presigned_url.await_args_list
    ] == [
        {"object_key": "masters/cooking.jpg", "expiration": 3600},
        {"object_key": "masters/cooking.png", "expiration": 3600},
    ]
    storage.download_object.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["", None])
async def test_missing_images_are_null_and_do_not_get_presigned(value):
    database = MockDatabase(
        initial_items=[
            {
                "scenePrincipal": "empty",
                "title": "Empty",
                "maxDurationSeconds": 5,
                "thumbnailUri": value,
                "guideUri": value,
            },
        ],
    )
    storage = AsyncMock()
    result = await attach_scene_master_urls(
        scenes=await get_scene_masters(scenes_db=database),
        storage=storage,
    )
    assert result[0].thumbnail_url is None
    assert result[0].guide_url is None
    storage.generate_presigned_url.assert_not_awaited()
