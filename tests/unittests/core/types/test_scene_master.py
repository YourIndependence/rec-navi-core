# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Scene master URL and persistence boundaries."""

from unittest.mock import AsyncMock

import pytest

from recnavi.core.types.scene_master import SceneMaster
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_master_urls_are_refreshed_without_losing_durable_references():
    master = SceneMaster(
        scene_principal="opening",
        title="Opening",
        max_duration_seconds=30,
        thumbnail_uri="masters/example.jpg",
        guide_uri="masters/guide.png",
    )
    original = master.to_storage_item()
    storage = MockObjectStorage(bucket_name="media")
    storage.generate_presigned_url = AsyncMock(
        side_effect=[
            "https://signed/example-1",
            "https://signed/guide-1",
            "https://signed/example-2",
            "https://signed/guide-2",
        ],
    )
    first = await master.attach_presigned_url(storage=storage)
    second = await first.attach_presigned_url(storage=storage)
    assert master.thumbnail_url is None
    assert first.thumbnail_url == "https://signed/example-1"
    assert second.thumbnail_url == "https://signed/example-2"
    assert second.guide_url == "https://signed/guide-2"
    assert first.to_storage_item() == second.to_storage_item() == original
    restored = SceneMaster.model_validate(second.to_storage_item())
    assert restored.thumbnail_uri == master.thumbnail_uri
    assert restored.guide_uri == master.guide_uri
    assert restored.thumbnail_url is None
    assert second.model_dump(by_alias=True) == {
        "scenePrincipal": "opening",
        "title": "Opening",
        "maxDurationSeconds": 30,
        "thumbnailUrl": "https://signed/example-2",
        "guideUrl": "https://signed/guide-2",
    }


def test_master_response_schema_excludes_storage_references():
    properties = SceneMaster.model_json_schema(mode="serialization")[
        "properties"
    ]
    assert "thumbnailUri" not in properties
    assert "guideUri" not in properties
    assert "thumbnailUrl" in properties
    assert "guideUrl" in properties
