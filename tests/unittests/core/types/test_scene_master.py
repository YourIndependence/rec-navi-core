# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Scene master URL and persistence boundaries."""

from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from recnavi.core.types.scene_master import SceneMaster
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_master_urls_are_refreshed_without_losing_durable_references():
    master = SceneMaster(
        scene_principal="opening",
        title="Opening",
        max_duration_seconds=5,
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
    assert first is master
    assert master.thumbnail_url == "https://signed/example-1"
    second = await master.attach_presigned_url(storage=storage)
    assert second is master
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
        "maxDurationSeconds": 5,
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


@pytest.mark.parametrize("duration", [0, 11])
def test_master_rejects_duration_outside_bounds(duration):
    """Enforce the recording duration invariant in the domain model."""
    with pytest.raises(ValidationError):
        SceneMaster(
            scene_principal="opening",
            title="Opening",
            max_duration_seconds=duration,
        )


@pytest.mark.parametrize("duration", [1, 10])
def test_master_accepts_duration_boundaries(duration):
    """Accept both ends of the supported recording duration range."""
    master = SceneMaster(
        scene_principal="opening",
        title="Opening",
        max_duration_seconds=duration,
    )
    assert master.max_duration_seconds == duration


@pytest.mark.parametrize("principal", ["", "../other", "nested/key"])
def test_master_rejects_invalid_principal(principal):
    with pytest.raises(ValidationError):
        SceneMaster(
            scene_principal=principal,
            title="Shop",
            max_duration_seconds=5,
        )


@pytest.mark.asyncio
async def test_master_updates_images_without_persisting_payloads():
    master = SceneMaster(
        scene_principal="shop",
        title="Shop",
        max_duration_seconds=5,
    )
    storage = MockObjectStorage(bucket_name="media")
    async with master.update_images(
        storage=storage,
        bucket_name="media",
        example_image="ZXhhbXBsZQ==",
        guide_image="Z3VpZGU=",
    ) as result:
        assert result is master
        assert master.thumbnail_uri.startswith("s3://media/scenes/shop/")
        assert master.thumbnail_uri.endswith("/example.jpg")
        assert (
            master.guide_uri
            == master.thumbnail_uri.removesuffix("example.jpg") + "guide.jpg"
        )
    assert len(storage.objects) == 2
    assert "exampleImage" not in master.to_storage_item()
    assert "guideImage" not in master.to_storage_item()


@pytest.mark.asyncio
async def test_master_restores_references_when_persistence_fails():
    master = SceneMaster(
        scene_principal="shop",
        title="Shop",
        max_duration_seconds=5,
        thumbnail_uri="s3://media/scenes/shop/old/example.jpg",
        guide_uri="s3://media/scenes/shop/old/guide.jpg",
    )
    previous = master.to_storage_item()
    storage = MockObjectStorage(bucket_name="media")
    with pytest.raises(OSError, match="persistence failed"):
        async with master.update_images(
            storage=storage,
            bucket_name="media",
            example_image="ZXhhbXBsZQ==",
            guide_image="Z3VpZGU=",
        ):
            raise OSError("persistence failed")
    assert master.to_storage_item() == previous
    assert storage.objects == {}
