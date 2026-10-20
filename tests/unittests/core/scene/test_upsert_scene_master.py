# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for upsert_scene_master."""

import base64
import re

import pytest
from pydantic import ValidationError

from recnavi.core.scene.upsert_scene_master import update_scene_master
from recnavi.core.scene.upsert_scene_master import upsert_scene_master
from recnavi.core.types.scene_master import SceneMaster
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


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
    """Test model validation rejects maxDurationSeconds < 1."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))

    with pytest.raises(
        ValidationError,
        match="max_duration_seconds",
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
    """Test model validation rejects maxDurationSeconds > 10."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))

    with pytest.raises(
        ValidationError,
        match="max_duration_seconds",
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


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


async def _seed_existing(scenes_db: MockDatabase) -> None:
    await scenes_db.put_item(
        {
            "scenePrincipal": "existing_scene",
            "title": "Old Title",
            "maxDurationSeconds": 3,
            "thumbnailUri": "s3://test-bucket/scenes/existing_scene/example.jpg",
            "guideUri": "s3://test-bucket/scenes/existing_scene/guide.jpg",
        },
    )


@pytest.mark.asyncio
async def test_update_scene_master_creates_scene_with_images():
    """Test creating a new scene uploads both images as jpeg."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage(bucket_name="test-bucket")

    scene_master = await update_scene_master(
        scenes_db=scenes_db,
        scene_principal="new_scene",
        title="New Scene",
        max_duration_seconds=5,
        example_image=_b64(b"example"),
        guide_image=_b64(b"guide"),
        bucket_name="test-bucket",
        storage=storage,
    )

    assert isinstance(scene_master, SceneMaster)
    assert scene_master.scene_principal == "new_scene"
    assert scene_master.title == "New Scene"
    assert scene_master.max_duration_seconds == 5
    assert storage.objects == {
        ("test-bucket", "scenes/new_scene/example.jpg"): (
            b"example",
            "image/jpeg",
        ),
        ("test-bucket", "scenes/new_scene/guide.jpg"): (
            b"guide",
            "image/jpeg",
        ),
    }


@pytest.mark.asyncio
async def test_update_scene_master_updates_scene_without_images():
    """Test updating an existing scene without images uploads nothing."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    await _seed_existing(scenes_db)
    storage = MockObjectStorage(bucket_name="test-bucket")

    scene_master = await update_scene_master(
        scenes_db=scenes_db,
        scene_principal="existing_scene",
        title="Updated Title",
        max_duration_seconds=7,
        example_image=None,
        guide_image=None,
        bucket_name="test-bucket",
        storage=storage,
    )

    assert isinstance(scene_master, SceneMaster)
    assert scene_master.title == "Updated Title"
    assert scene_master.max_duration_seconds == 7
    assert (
        scene_master.thumbnail_uri
        == "s3://test-bucket/scenes/existing_scene/example.jpg"
    )
    assert (
        scene_master.guide_uri
        == "s3://test-bucket/scenes/existing_scene/guide.jpg"
    )
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_update_scene_master_raises_422_when_images_missing_on_create():
    """Test creating without images raises 422 and uploads nothing."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage(bucket_name="test-bucket")

    with pytest.raises(
        ClientUnprocessableEntityError,
        match="exampleImage and guideImage are required when creating a new scene",
    ):
        await update_scene_master(
            scenes_db=scenes_db,
            scene_principal="new_scene",
            title="New Scene",
            max_duration_seconds=5,
            example_image=None,
            guide_image=None,
            bucket_name="test-bucket",
            storage=storage,
        )

    assert storage.objects == {}


@pytest.mark.asyncio
async def test_update_scene_master_updates_only_example_image():
    """Test only the provided example image is uploaded."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    await _seed_existing(scenes_db)
    storage = MockObjectStorage(bucket_name="test-bucket")

    scene_master = await update_scene_master(
        scenes_db=scenes_db,
        scene_principal="existing_scene",
        title="Title",
        max_duration_seconds=5,
        example_image=_b64(b"new_example"),
        guide_image=None,
        bucket_name="test-bucket",
        storage=storage,
    )

    assert isinstance(scene_master, SceneMaster)
    assert storage.objects == {
        ("test-bucket", "scenes/existing_scene/example.jpg"): (
            b"new_example",
            "image/jpeg",
        ),
    }


@pytest.mark.asyncio
async def test_update_scene_master_updates_only_guide_image():
    """Test only the provided guide image is uploaded."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    await _seed_existing(scenes_db)
    storage = MockObjectStorage(bucket_name="test-bucket")

    await update_scene_master(
        scenes_db=scenes_db,
        scene_principal="existing_scene",
        title="Title",
        max_duration_seconds=5,
        example_image=None,
        guide_image=_b64(b"new_guide"),
        bucket_name="test-bucket",
        storage=storage,
    )

    assert storage.objects == {
        ("test-bucket", "scenes/existing_scene/guide.jpg"): (
            b"new_guide",
            "image/jpeg",
        ),
    }


@pytest.mark.asyncio
async def test_update_scene_master_issues_new_id_when_principal_is_null():
    """Test a null scenePrincipal creates a scene with an issued id."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage(bucket_name="test-bucket")

    scene_master = await update_scene_master(
        scenes_db=scenes_db,
        scene_principal=None,
        title="New Scene",
        max_duration_seconds=5,
        example_image=_b64(b"example"),
        guide_image=_b64(b"guide"),
        bucket_name="test-bucket",
        storage=storage,
    )

    assert isinstance(scene_master, SceneMaster)
    issued_id = scene_master.scene_principal
    assert re.fullmatch(r"[0-9a-f]{32}", issued_id)
    assert (
        scene_master.thumbnail_uri
        == f"s3://test-bucket/scenes/{issued_id}/example.jpg"
    )
    assert ("test-bucket", f"scenes/{issued_id}/guide.jpg") in storage.objects
    stored = await scenes_db.get_item({"scenePrincipal": issued_id})
    assert stored["title"] == "New Scene"


@pytest.mark.asyncio
async def test_update_scene_master_raises_422_when_null_principal_without_images():
    """Test creating via a null id still requires both images."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage(bucket_name="test-bucket")

    with pytest.raises(ClientUnprocessableEntityError):
        await update_scene_master(
            scenes_db=scenes_db,
            scene_principal=None,
            title="New Scene",
            max_duration_seconds=5,
            example_image=_b64(b"example"),
            guide_image=None,
            bucket_name="test-bucket",
            storage=storage,
        )

    assert storage.objects == {}
    assert (await scenes_db.scan()).items == []
