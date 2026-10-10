# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for update_scene."""

import base64
import re

import pytest

from recnavi.core.scene.upsert_scene_master import update_scene
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


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
async def test_update_scene_creates_scene_with_images():
    """Test creating a new scene uploads both images as jpeg."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage()

    scenes = await update_scene(
        scenes_db=scenes_db,
        scene_principal="new_scene",
        title="New Scene",
        max_duration_seconds=5,
        example_image=_b64(b"example"),
        guide_image=_b64(b"guide"),
        bucket_name="test-bucket",
        storage=storage,
    )

    assert len(scenes) == 1
    assert scenes[0].scene_principal == "new_scene"
    assert scenes[0].title == "New Scene"
    assert scenes[0].max_duration_seconds == 5
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
async def test_update_scene_updates_scene_without_images():
    """Test updating an existing scene without images uploads nothing."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    await _seed_existing(scenes_db)
    storage = MockObjectStorage()

    scenes = await update_scene(
        scenes_db=scenes_db,
        scene_principal="existing_scene",
        title="Updated Title",
        max_duration_seconds=7,
        example_image=None,
        guide_image=None,
        bucket_name="test-bucket",
        storage=storage,
    )

    assert len(scenes) == 1
    assert scenes[0].title == "Updated Title"
    assert scenes[0].max_duration_seconds == 7
    assert (
        scenes[0].thumbnail_uri
        == "s3://test-bucket/scenes/existing_scene/example.jpg"
    )
    assert (
        scenes[0].guide_uri
        == "s3://test-bucket/scenes/existing_scene/guide.jpg"
    )
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_update_scene_raises_422_when_images_missing_on_create():
    """Test creating without images raises 422 and uploads nothing."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage()

    with pytest.raises(
        ClientUnprocessableEntityError,
        match="exampleImage and guideImage are required when creating a new scene",
    ):
        await update_scene(
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
async def test_update_scene_updates_only_example_image():
    """Test only the provided example image is uploaded."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    await _seed_existing(scenes_db)
    storage = MockObjectStorage()

    scenes = await update_scene(
        scenes_db=scenes_db,
        scene_principal="existing_scene",
        title="Title",
        max_duration_seconds=5,
        example_image=_b64(b"new_example"),
        guide_image=None,
        bucket_name="test-bucket",
        storage=storage,
    )

    assert len(scenes) == 1
    assert storage.objects == {
        ("test-bucket", "scenes/existing_scene/example.jpg"): (
            b"new_example",
            "image/jpeg",
        ),
    }


@pytest.mark.asyncio
async def test_update_scene_updates_only_guide_image():
    """Test only the provided guide image is uploaded."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    await _seed_existing(scenes_db)
    storage = MockObjectStorage()

    await update_scene(
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
async def test_update_scene_issues_new_id_when_principal_is_null():
    """Test a null scenePrincipal creates a scene with an issued id."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage()

    scenes = await update_scene(
        scenes_db=scenes_db,
        scene_principal=None,
        title="New Scene",
        max_duration_seconds=5,
        example_image=_b64(b"example"),
        guide_image=_b64(b"guide"),
        bucket_name="test-bucket",
        storage=storage,
    )

    assert len(scenes) == 1
    issued_id = scenes[0].scene_principal
    assert re.fullmatch(r"[0-9a-f]{32}", issued_id)
    assert (
        scenes[0].thumbnail_uri
        == f"s3://test-bucket/scenes/{issued_id}/example.jpg"
    )
    assert ("test-bucket", f"scenes/{issued_id}/guide.jpg") in storage.objects
    stored = await scenes_db.get_item({"scenePrincipal": issued_id})
    assert stored["title"] == "New Scene"


@pytest.mark.asyncio
async def test_update_scene_raises_422_when_null_principal_without_images():
    """Test creating via a null id still requires both images."""
    scenes_db = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage()

    with pytest.raises(ClientUnprocessableEntityError):
        await update_scene(
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
