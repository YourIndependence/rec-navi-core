# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for upsert_scene_master."""

import pytest

from recnavi.core.scene.upsert_scene_master import upsert_scene_master
from recnavi.core.types.scene_master import SceneMaster
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_upsert_scene_master_creates_new_scene():
    """Test upsert creates new scene master when it doesn't exist."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))

    result = await upsert_scene_master(
        scenes_db=scenes_db,
        scene_principal="new_scene",
        title="New Scene",
        max_duration_seconds=5,
        thumbnail_uri="s3://bucket/scenes/new_scene/example.jpg",
        guide_uri="s3://bucket/scenes/new_scene/guide.jpg",
    )

    assert isinstance(result, SceneMaster)
    assert result.scene_principal == "new_scene"
    assert result.title == "New Scene"
    assert result.max_duration_seconds == 5
    assert result.thumbnail_uri == "s3://bucket/scenes/new_scene/example.jpg"
    assert result.guide_uri == "s3://bucket/scenes/new_scene/guide.jpg"

    stored_item = await scenes_db.get_item({"scenePrincipal": "new_scene"})
    assert stored_item is not None
    assert stored_item["title"] == "New Scene"


@pytest.mark.asyncio
async def test_upsert_scene_master_updates_existing_scene():
    """Test upsert updates existing scene master."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    await scenes_db.put_item(
        {
            "scenePrincipal": "existing_scene",
            "title": "Old Title",
            "maxDurationSeconds": 3,
            "thumbnailUri": "s3://bucket/old_example.jpg",
            "guideUri": "s3://bucket/old_guide.jpg",
        },
    )

    result = await upsert_scene_master(
        scenes_db=scenes_db,
        scene_principal="existing_scene",
        title="Updated Title",
        max_duration_seconds=7,
        thumbnail_uri="s3://bucket/new_example.jpg",
        guide_uri="s3://bucket/new_guide.jpg",
    )

    assert isinstance(result, SceneMaster)
    assert result.scene_principal == "existing_scene"
    assert result.title == "Updated Title"
    assert result.max_duration_seconds == 7
    assert result.thumbnail_uri == "s3://bucket/new_example.jpg"
    assert result.guide_uri == "s3://bucket/new_guide.jpg"

    stored_item = await scenes_db.get_item(
        {"scenePrincipal": "existing_scene"},
    )
    assert stored_item["title"] == "Updated Title"
    assert stored_item["maxDurationSeconds"] == 7


@pytest.mark.asyncio
async def test_upsert_scene_master_validates_max_duration_min():
    """Test upsert raises 422 when maxDurationSeconds < 1."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))

    with pytest.raises(
        ClientUnprocessableEntityError,
        match="maxDurationSeconds must be between 1 and 10 seconds",
    ):
        await upsert_scene_master(
            scenes_db=scenes_db,
            scene_principal="invalid_scene",
            title="Invalid Scene",
            max_duration_seconds=0,
            thumbnail_uri="s3://bucket/example.jpg",
            guide_uri="s3://bucket/guide.jpg",
        )


@pytest.mark.asyncio
async def test_upsert_scene_master_validates_max_duration_max():
    """Test upsert raises 422 when maxDurationSeconds > 10."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))

    with pytest.raises(
        ClientUnprocessableEntityError,
        match="maxDurationSeconds must be between 1 and 10 seconds",
    ):
        await upsert_scene_master(
            scenes_db=scenes_db,
            scene_principal="invalid_scene",
            title="Invalid Scene",
            max_duration_seconds=11,
            thumbnail_uri="s3://bucket/example.jpg",
            guide_uri="s3://bucket/guide.jpg",
        )


@pytest.mark.asyncio
async def test_upsert_scene_master_allows_valid_range():
    """Test upsert accepts maxDurationSeconds from 1 to 10."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))

    for duration in [1, 5, 10]:
        result = await upsert_scene_master(
            scenes_db=scenes_db,
            scene_principal=f"scene_{duration}",
            title=f"Scene {duration}",
            max_duration_seconds=duration,
            thumbnail_uri="s3://bucket/example.jpg",
            guide_uri="s3://bucket/guide.jpg",
        )
        assert result.max_duration_seconds == duration
